from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date

class ContractRequest(models.Model):
    _name = 'contract.request'
    _description = 'Contract Request for Supply'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Subject', 
        required=True, 
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string='Organization Name', 
        required=True,
        tracking=True,
        help="The external organization/customer you are writing to."
    )
    recipient_office = fields.Char(
        string='Recipient Office / Directorate', 
        help="E.g., Procurement Directorate, Finance Office"
    )
    city = fields.Char(
        string='City',
        compute='_compute_city',
        store=True,
        readonly=False,
        help="City of the organization. Defaults to partner's city."
    )
    request_date = fields.Date(
        string='Date', 
        default=fields.Date.context_today,
        required=True
    )
    goods_description = fields.Text(
        string='Brief Description of Goods/Services',
        required=True,
        help="The text to replace [brief description of goods/services] in the letter."
    )
    line_ids = fields.One2many(
        'contract.request.line', 
        'request_id', 
        string='Items Available'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('accepted', 'Accepted'),
        ('agreement_created', 'Agreement Created'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    requester_id = fields.Many2one(
        'res.users', 
        string='Sender/Requester', 
        default=lambda self: self.env.user,
        readonly=True
    )
    agreement_ids = fields.Many2many('sale.order', string="Agreements", readonly=True)
    agreement_count = fields.Integer(string="Agreement Count", compute='_compute_agreement_count')
    
    @api.depends('agreement_ids')
    def _compute_agreement_count(self):
        for record in self:
            record.agreement_count = len(record.agreement_ids)

    @api.depends('partner_id')
    def _compute_city(self):
        """Auto-fill city based on the selected partner"""
        for record in self:
            if record.partner_id and record.partner_id.city:
                record.city = record.partner_id.city

    def action_submit(self):
        self.ensure_one()
        if not self.goods_description:
            raise UserError(_("Please provide a brief description of the goods before submitting."))
        self.state = 'submitted'

    def action_approve(self):
        self.state = 'approved'

    def action_customer_approve(self):
        # Customer has sent a positive response
        self.state = 'accepted'

    def action_reject(self):
        self.state = 'rejected'

    def action_reset_draft(self):
        self.state = 'draft'

    def action_create_agreement(self):
            self.ensure_one()
            agreement_lines = []
            for line in self.line_ids:
                agreement_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'description': line.product_id.name,
                    'quantity': line.quantity,
                    'uom_id': line.uom_id.id,
                }))

            return {
                'type': 'ir.actions.act_window',
                'name': 'Create Agreement',
                'res_model': 'sale.agreement',
                'view_mode': 'form',
                'view_id': False,
                'target': 'current',
                'context': {
                    'default_name': self.name,
                    'default_partner_id': self.partner_id.id,
                    'default_contract_request_id': self.id,
                    'default_line_ids': agreement_lines,
                    'default_start_date': fields.Date.today(),
                    'default_source_from': 'contract',
                }
            }

    def action_view_agreements(self):
        return {
            'name': 'Related Agreements',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'sale.agreement',
            'domain': [('request_id', '=', self.id)],
            'context': {'default_request_id': self.id}
        }

class ContractRequestLine(models.Model):
    """
    Helper model to list specific items if 'goods_description' 
    needs to be detailed or generated from existing products.
    """
    _name = 'contract.request.line'
    _description = 'Contract Request Line'

    request_id = fields.Many2one('contract.request', string='Request')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Available Qty')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')