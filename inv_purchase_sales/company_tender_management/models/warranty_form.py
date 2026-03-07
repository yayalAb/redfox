from odoo import models, fields, api

class BidWarrantyLetter(models.Model):
    _name = 'bid.warranty.letter'
    _description = 'Bid Warranty Letter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_issue desc, id desc'

    name = fields.Char(
        string='Reference', 
        required=True, 
        copy=False, 
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        required=True, 
        default=lambda self: self.env.company
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string='Purchaser / Client', 
        required=True,
        tracking=True
    )
    tender_reference = fields.Char(
        string='Reference No. (Tender)', 
        required=True,
        tracking=True
    )
    date_issue = fields.Date(
        string='Date', 
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    goods_description = fields.Text(
        string='Description of Goods', 
        required=True,
        help="Description of the goods being supplied/warranted."
    )
    warranty_period = fields.Char(
        string='Warranty Period', 
        required=True,
        help="e.g. 1 Year, 24 Months, etc."
    )
    signatory_id = fields.Many2one(
        'res.users', 
        string='Authorized Signatory', 
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    signatory_title = fields.Char(
        string='Signatory Title',
        related='signatory_id.partner_id.function',
        readonly=False,
        store=True
    )
    tender_id = fields.Many2one('tender.request', string='Related Tender', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('bid.warranty.letter') or 'New'
        return super(BidWarrantyLetter, self).create(vals)