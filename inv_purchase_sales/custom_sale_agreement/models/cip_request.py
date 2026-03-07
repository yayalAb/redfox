from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CIPRequest(models.Model):
    _name = 'cip.request'
    _description = 'CIP Request'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Added tracking support

    name = fields.Char(string='Request Name', required=True, copy=False, 
                       readonly=False, default=lambda self: _('New'))
    
    # LOGICAL STATE SELECTION
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft', string='Status', tracking=True)

    requester_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user, tracking=True)
    proposed_date = fields.Date(string='Proposed Date', tracking=True)
    inspection_place = fields.Char(string='Inspection Place')
    
    supplier_name = fields.Char(string='Name of Supplier/Manufacturer')
    contract_date = fields.Date(string='Contract Date')
    contract_name = fields.Char(string='Contract Name')

    agreement_id = fields.Many2one('sale.agreement', string="Source Agreement") 
    line_ids = fields.One2many('cip.request.line', 'cip_request_id', string='Request Lines')

    # --- WORKFLOW ACTIONS ---
    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Only draft requests can be submitted."))
            rec.state = 'submitted'

    def action_review(self):
        for rec in self:
            if rec.state != 'submitted':
                raise ValidationError(_("Request must be Submitted before Review."))
            rec.state = 'review'

    def action_approve(self):
        for rec in self:
            if rec.state != 'review':
                raise ValidationError(_("Request must be Reviewed before Approval."))
            rec.state = 'approved'

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'


class CIPRequestLine(models.Model):
    _name = 'cip.request.line'
    _description = 'CIP Request Line'

    cip_request_id = fields.Many2one('cip.request')
    product_id = fields.Many2one('product.product', required=True)
    quantity_total = fields.Integer(string='Quantity Total (contract)')
    quantity_accepted = fields.Integer(string='Quantity Accepted up to date')
    quantity_offered = fields.Integer(string='Quantity Offered (Now)')