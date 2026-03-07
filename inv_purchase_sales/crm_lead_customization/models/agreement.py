from odoo import fields, models
class Agreement(models.Model):
    _inherit = 'sale.agreement' # Use the correct model name for your agreements

    lead_id = fields.Many2one('crm.lead', string='Opportunity')