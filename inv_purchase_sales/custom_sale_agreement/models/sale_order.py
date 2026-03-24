# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # --- CATEGORY & MRP FIELDS ---
    sale_category = fields.Selection([
        ('product_sale', 'Product Sale'),
        ('maintenance', 'Maintenance'),
        ('test', 'Test')
    ])
    
    mrp_ids = fields.Many2one('mrp.production', string='Manufacturing Orders')
    mrp_count = fields.Integer(string="MRP Count", compute='_compute_mrp_count')

    # --- PAYMENT REQUEST FIELDS ---
    # Merged from sale_order_extension.py
    payment_request_ids = fields.One2many('payment.request', 'sale_order_id', string='Payment Requests')
    payment_request_count = fields.Integer(string="Payment Requests", compute='_compute_payment_request_count')

    # --- REPORTING FIELDS ---
    report_remark = fields.Text(string='Report Remark', 
                                help="Text to appear in the Remark section of the printout")
    partner_tin = fields.Char(string='TIN', help="Tax Identification Number")
    
    # agreement_id = fields.Many2one('sale.agreement', string="Source Agreement")
    contract_ref = fields.Char(string='Contract No', help="Reference to the Agreement/Contract")

    # mrp_ids = fields.Many2one('mrp.production', string='Manufacturing Orders')
    # mrp_count = fields.Integer(
    #     string="MRP Count", compute='_compute_mrp_count')
    state = fields.Selection(
        selection=[
            ('draft', "Quotation Draft"),
            ('quotation_submit', "Quotation Submitted"),
            ('quotation_review', "Quotation Reviewed"),
            ('quotation_approve', "Quotation Approved"),
            ('quotation_refuse', "Quotation Refused"),
            ('sent', "Quotation Sent"),
            ('order_submit', 'Order Submitted'),
            ('order_review', 'Order Reviewed'),
            ('sale', "Sales Order"),
            ('cancel', "Cancelled"),
        ], string="Status", readonly=True, copy=False, index=True, tracking=3, default='draft')

    order_type = fields.Selection([
        ('quotation', 'Quotation'), ('order', 'Order')
    ], default='quotation', string='Order Type')

    # --- SIGNATURE FIELDS ---
    prepared_by_id = fields.Many2one('res.users', string='Prepared By', readonly=True)
    prepared_date = fields.Date(string='Prepared Date', readonly=True)
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Date(string='Approved Date', readonly=True)

    # --- CONSTRAINTS & ONCHANGES ---

    @api.constrains('sale_category')
    def _check_sale_category(self):
        for order in self:
            if order.state == 'order_submit' and not order.sale_category:
                raise ValidationError("please select sale category before submitting order.")
    
    @api.onchange('partner_id')
    def _onchange_partner_id_tin(self):
        if self.partner_id:
            self.partner_tin = self.partner_id.vat or ""
        else:
            self.partner_tin = ""

    @api.onchange('agreement_id')
    def _onchange_agreement_id_contract(self):
        if self.agreement_id:
            self.contract_ref = self.agreement_id.code or self.agreement_id.name
        else:
            self.contract_ref = ""

    @api.depends('payment_request_ids')
    def _compute_payment_request_count(self):
        for order in self:
            order.payment_request_count = len(order.payment_request_ids)
            
    def _compute_mrp_count(self):
        for record in self:
            record.mrp_count = self.env['mrp.production'].search_count([('origin', '=', record.name)])

    # --- CREATE OVERRIDE ---
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.quotation') or _('New')
        return super(SaleOrder, self).create(vals_list)

    # --- WORKFLOW ACTIONS ---

    def action_quotation_submit(self):
        for order in self:
            order.write({
                'state': 'quotation_submit',
                'prepared_by_id': self.env.user.id,
                'prepared_date': fields.Date.today()
            })

    def action_quotation_review(self):
        for order in self:
            order.write({'state': 'quotation_review'})

    def action_quotation_approve(self):
        for order in self:
            order.write({'state': 'quotation_approve'})

    def action_quotation_reject(self):
        for order in self:
            order.write({'state': 'quotation_refuse'})

    def action_quotation_reset_to_draft(self):
        for order in self:
            order.write({'state': 'draft'})
            
    def action_submit_order(self):
        for order in self:
            name = self.env['ir.sequence'].next_by_code('sale.order') or _('New')
            order.write({
                'name': name, 
                'state': 'order_submit', 
                'order_type': 'order',
                'prepared_by_id': self.env.user.id,
                'prepared_date': fields.Date.today()
            })
            
    def action_review_order(self):
        for order in self:
            order.write({'state': 'order_review'})

    def action_confirm(self):
        for order in self:
            if not order.order_line:
                raise ValidationError(_("You cannot confirm a sales order without any product lines."))
        
        res = super(SaleOrder, self).action_confirm()
        
        for order in self:
            order.write({
                'approved_by_id': self.env.user.id,
                'approved_date': fields.Date.today()
            })
        return res

    def _confirmation_error_message(self):
        self.ensure_one()
        if self.state not in {'order_review'}:
            return _("Some orders are not in a state requiring confirmation.")
        if any(not line.display_type and not line.is_downpayment and not line.product_id for line in self.order_line):
            return _("A line on these orders missing a product, you cannot confirm it.")
        return False

    # --- PAYMENT REQUEST ACTIONS (Merged) ---

    def action_create_payment_request(self):
        self.ensure_one()
        if self.state not in ['sale', 'done']:
            raise ValidationError(_("You can only create a payment request for confirmed Sales Orders."))

        req_lines = []
        for line in self.order_line:
            if not line.display_type:
                req_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.product_uom_qty,
                    'uom_id': line.product_uom.id,
                    'price_unit': line.price_unit,
                }))

        vals = {
            'sale_order_id': self.id,
            'partner_id': self.partner_id.id,
            'line_ids': req_lines,
            'subject': f"Payment Request for Order {self.name}",
            'department_name': 'Sourcing Contract Management', 
        }

        if hasattr(self, 'agreement_id') and self.agreement_id:
            vals['agreement_id'] = self.agreement_id.id
            ref_date = self.agreement_id.signature_date or fields.Date.today()
            ref_no = self.agreement_id.code or "N/A"
            vals['contract_ref_text'] = f"Ref: purchase orders No: {ref_no} Dated {ref_date}"

        request = self.env['payment.request'].create(vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Request',
            'res_model': 'payment.request',
            'res_id': request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_payment_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Requests',
            'res_model': 'payment.request',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id}
        }


        
    # def _compute_mrp_count(self):
    #     for record in self:
    #         record.mrp_count = self.env['mrp.production'].search_count(
    #             [('origin', '=', record.name)])

    # def action_create_mrp(self):
    #     """
    #     Creates a separate Manufacturing Order for each Sales Order Line
    #     ONLY if the product has the 'Manufacture' route configured.
    #     """
    #     mrp_production = self.env['mrp.production']
    #     manufacture_route = self.env.ref('mrp.route_warehouse0_manufacture')

    #     for order in self:
    #         created_mrps = False

    #         for line in order.order_line:
    #             # 1. Skip sections/notes or products with 0 qty
    #             if line.display_type or line.product_uom_qty <= 0:
    #                 continue

    #             product_routes = line.product_id.route_ids | line.product_id.categ_id.route_ids

    #             if manufacture_route in product_routes:

    #                 mrp_vals = {
    #                     'product_id': line.product_id.id,
    #                     'product_qty': line.product_uom_qty,
    #                     'product_uom_id': line.product_uom.id,
    #                     'origin': order.name,
    #                     'company_id': order.company_id.id,
    #                 }

    #                 mrp_production.create(mrp_vals)
    #                 created_mrps = True

    #         if not created_mrps:
    #             raise UserError(
    #                 _("No lines found with the 'Manufacture' route to create orders."))

    #     # Redirect to the view showing all created MOs
    #     return self.action_view_mrp()

    # def action_view_mrp(self):
    #     """
    #     View function: Shows list of MOs if multiple, or form view if only one.
    #     """
    #     self.ensure_one()
    #     domain = [('origin', '=', self.name)]
    #     mrp_ids = self.env['mrp.production'].search(domain).ids

    #     action = {
    #         'name': _('Manufacturing Orders'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'mrp.production',
    #         'domain': domain,
    #         'context': {'default_origin': self.name},
    #     }

    #     if len(mrp_ids) == 1:
    #         action['view_mode'] = 'form'
    #         action['res_id'] = mrp_ids[0]
    #     else:
    #         action['view_mode'] = 'list,form'

    #     return action
