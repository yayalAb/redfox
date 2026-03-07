from odoo import models, fields

class StoreRequest(models.Model):
    _inherit = 'store.request'

    maintenance_request_id = fields.Many2one(
        'maintenance.request', 
        string='Source Maintenance Request',
        readonly=True,
        copy=False
    )