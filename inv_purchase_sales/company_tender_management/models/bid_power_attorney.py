from odoo import models, fields, api

class BidPowerAttorney(models.Model):
    _name = 'bid.power.attorney'
    _description = 'Bid Power of Attorney'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(
        string='Reference', 
        required=True, 
        copy=False,  
        default='New',
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company', 
        string='Bidder Name', 
        required=True, 
        default=lambda self: self.env.company
    )
    procuring_entity_id = fields.Many2one(
        'res.partner', 
        string='Procuring Entity / Client', 
        required=True,
        tracking=True
    )
    goods_description = fields.Text(
        string='Goods / Services Description', 
        required=True,
        help="Description of what the company supplies (e.g., IT Equipment, Construction Materials)"
    )
    representative_id = fields.Many2one(
        'res.partner', 
        string='Authorized Representative', 
        required=True,
        help="The person being given the power of attorney"
    )
    tender_description = fields.Text(
        string='Procurement / Tender Description', 
        required=True,
        tracking=True
    )
    bid_reference = fields.Char(
        string='Bid Reference Number', 
        required=True,
        tracking=True
    )

    official_id = fields.Many2one(
        'res.users', 
        string='Authorized Company Official', 
        default=lambda self: self.env.user,
        required=True
    )
    
    official_title = fields.Char(
        string='Official Title',
        related='official_id.partner_id.function',
        readonly=False,
        store=True
    )

    date_issue = fields.Date(
        string='Date', 
        default=fields.Date.context_today
    )
    tender_id = fields.Many2one('tender.request', string='Related Tender')
