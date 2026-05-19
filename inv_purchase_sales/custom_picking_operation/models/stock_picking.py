# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    vehicle_plate = fields.Char(string='Truck / Plate No.')
    reason_for_entry = fields.Text(string='Reason')
