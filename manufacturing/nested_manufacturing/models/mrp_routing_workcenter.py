from odoo import models, fields, api


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    product_id= fields.Many2one(
        'product.product',
        string='Final Output',
    )
    workorder_type_id = fields.Many2one('workorder.type', string='Workorder Type', required=True)

