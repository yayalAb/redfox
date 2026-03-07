from odoo import models, fields

class Agreement(models.Model):
    _inherit = 'sale.agreement'

    tender_id = fields.Many2one(
        'tender.request',
        string='Originating Tender',
        ondelete='set null',
        readonly=True,
        copy=False 
    )