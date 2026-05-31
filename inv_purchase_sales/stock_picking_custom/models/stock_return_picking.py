from odoo import fields, models


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    picking_type_code = fields.Selection(related='picking_id.picking_type_code')
    picking_type_id = fields.Many2one(related='picking_id.picking_type_id')
