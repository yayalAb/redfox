from odoo import models, fields, api, Command
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict


class SuppliesRfp(models.Model):

    _name = 'supplies.rfp'
    _inherit = ['mail.thread']
    _description = 'Purchase Request'
    _rec_name = 'rfp_number'
    _order = 'requested_date desc'

    rfp_number = fields.Char(
        string='RFP Number', index=True, default='New')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('evaluation', 'Evaluation'),
        ('accepted', 'Accepted'),
        ('ordered', 'Ordered'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], string='Status', readonly=True, index=True, tracking=True, default='draft')
    purchase_origin = fields.Selection([
        ('local', 'Local'), ('foreign', 'Foreign')],
        string='Purchase Origin', required=True, default='local')
    purchase_type = fields.Selection([
        ('bid', 'Bid'),
        ('direct', 'Direct'),
        ('proforma', 'Proforma Invoice'),
        ('petty_cash', 'Petty Cash'),
    ], string='Purchase Method', default='proforma')
    product_line_ids = fields.One2many(
        'supplies.rfp.line', 'rfp_id', string='Product Lines')
    rfq_ids = fields.One2many('purchase.order', 'rfp_id',
                              string='Quotations', domain=lambda self: self._get_rfq_domain())
    rfq_count = fields.Integer(
        string='Number of RFQs', compute='_compute_rfq_count', store=False)
    rfq_line_ids = fields.One2many('purchase.order.line', 'rfp_id',
                                   compute='_compute_rfq_line_ids', string='Quotation Lines', store=True)
    store_request_id = fields.Many2one(
        'store.request', string='Store Request', readonly=True)
    product_category_id = fields.Many2one(
        'product.category', string="Product Category", required=True)
    purpose = fields.Text(string='Purpose')
    total_amount = fields.Monetary(
        string='Total Amount', compute='_compute_total_amount', store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    company_id = fields.Many2one(
        'res.company', string='Company', tracking=True, default=lambda self: self.env.company.id)
    department_id = fields.Many2one(
        'hr.department', string='Department', tracking=True)
    committee_member_ids = fields.One2many(
        'committee.member', 'rfp_id', string='Committee Members')

    requested_date = fields.Datetime(
        string='Requested Date', required=True, default=fields.Datetime.now, tracking=True)
    required_date = fields.Date(string='Required Date', tracking=True,
                                default=lambda self: fields.Date.add(fields.Date.today(), days=5))
    date_approve = fields.Date(string='Reviewed On', readonly=True)
    date_ordered = fields.Date(string='Ordered On', readonly=True)

    submitted_by = fields.Many2one(
        'res.users', string='Submitted By', readonly=True)
    approved_by = fields.Many2one(
        'res.users', string='Submitted By', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('rfp_number', 'New') == 'New':
                if vals.get('purchase_origin') == 'local':
                    prefix = 'PR'
                    sequence_code = 'purchase.request.local'
                    sequence_number = self.env['ir.sequence'].next_by_code(
                        sequence_code)
                    vals['rfp_number'] = f"{prefix.upper()}-{sequence_number}"
        return super(SuppliesRfp, self).create(vals_list)

    @api.onchange('store_request_id')
    def _onchange_store_request_id(self):
        if self.store_request_id:
            self.department_id = self.store_request_id.department_id
            self.company_id = self.store_request_id.company_id
            self.purpose = self.store_request_id.purpose

    @api.depends('rfq_ids.order_line')
    def _compute_rfq_line_ids(self):
        for rfp in self:
            rfp.rfq_line_ids = rfp.rfq_ids.mapped('order_line')

    @api.depends('rfq_ids')
    def _compute_rfq_count(self):
        for rec in self:
            rec.rfq_count = len(rec.rfq_ids)

    @api.model
    def _get_rfq_domain(self):
        domain = []
        for rec in self:
            domain = [('rfp_id', '=', rec.id)]
        return domain

    def action_submit(self):
        if not self.product_line_ids:
            raise UserError('Please add product lines before submitting.')

        if not all(self.product_line_ids.mapped('product_qty')):
            raise UserError('Product quantity must be greater than 0')

        self.write({'state': 'submitted', 'submitted_by': self.env.user.id, })

    def action_approve(self):
        self.write({'state': 'approved', 'date_approve': fields.Date.today(
        ), 'approved_by': self.env.user.id})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_close(self):
        self.write({'state': 'evaluation'})

    def action_accept(self):
        self.write({'state': 'accepted'})

    def action_return(self):
        for record in self:
            if record.state == 'approved':
                record.write({'state': 'submitted'})
            if record.state == 'evaluation':
                record.write({'state': 'approved'})
            elif record.state == 'accepted':
                record.write({'state': 'evaluation'})

    def action_view_quotations(self):
        self.ensure_one()
        return {
            'name': 'Quotations',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('rfp_id', '=', self.id), ('final_po', '=', False)],
            'type': 'ir.actions.act_window',
        }

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'name': 'Orders',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('rfp_id', '=', self.id), ('final_po', '=', True), ('state', '=', 'purchase')],
            'type': 'ir.actions.act_window',
        }

    @api.onchange('purchase_origin', 'state')
    def _onchange_purchase_origin(self):

        if not self.purchase_origin:
            return
        group_map = {
            'local': 'my_module.group_local_committee_users',
            'foreign': 'my_module.group_foreign_committee_users',
        }
        xml_id = group_map.get(self.purchase_origin)
        group = self.env.ref(xml_id, raise_if_not_found=False)

        if not group:
            self.committee_member_ids = [Command.clear()]
            return

        employees = self.env['hr.employee'].search([
            ('user_id', 'in', group.users.ids)
        ])
        new_members_list = [Command.clear()]

        for employee in employees:
            new_members_list.append(
                Command.create({
                    'member_id': employee.id,
                    'role': 'member',
                    'approval_status': 'pending',
                })
            )
        self.committee_member_ids = new_members_list
