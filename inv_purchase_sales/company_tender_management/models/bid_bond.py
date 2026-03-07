from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TenderBidBond(models.Model):
    _name = 'tender.bid.bond'
    _description = 'Outgoing Bid Bond Request'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Optional: for tracking changes

    bank_id = fields.Many2one('res.partner', string='To (Bank)', required=True, domain=[('category_id.name', 'ilike', 'Bank')])
    bank_city = fields.Char(string='City', default='Addis Ababa')

    beneficiary_id = fields.Many2one('res.partner', string='Beneficiary', help="e.g. Ethiopian Electric Utility")
    goods_description = fields.Char(string='Procurement Item', help="e.g. Different Rating Miniature Circuit Breaker (MCB)")
    tender_ref_no = fields.Char(string='Tender Ref No', help="e.g. EEU/DIST./NCB-005/2018 Lot-1")
    
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(string='Amount', currency_field='currency_id', required=True)
    amount_in_words = fields.Char(string='Amount in Words', help="e.g. Five hundred thousand Birr only")

    validity_days = fields.Integer(string='Validity (Days)', default=120)
    validity_start_date = fields.Date(string='Effective From')

    debit_account_no = fields.Char(string='Debit Account No', default='0090586510104')

    tender_id = fields.Many2one('tender.request', string='Related Tender Request')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status', tracking=True)

    # Helper to compute text (optional)
    @api.onchange('amount')
    def _onchange_amount(self):
        # In a real scenario, use num2words library here
        if self.amount:
            self.amount_in_words = f"{self.amount} Birr only (Auto-calc pending)"

    def action_approve(self):
        self.state = 'approved'

    def action_send(self):
        self.state = 'sent'