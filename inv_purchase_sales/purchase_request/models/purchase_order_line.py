from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    rfp_id = fields.Many2one('supplies.rfp', string='RFP', index=True, copy=False)

    recommended = fields.Boolean(string='Recommended', default=False)