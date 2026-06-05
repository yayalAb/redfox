# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    export_order_id = fields.Many2one('export.export.order', string='Export Order', copy=False)
    container_no = fields.Char(string='Container No.')
    seal_no = fields.Char(string='Seal No.')
