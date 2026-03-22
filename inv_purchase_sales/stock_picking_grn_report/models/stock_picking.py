# -*- coding: utf-8 -*-
from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    vehicle_plate = fields.Char(string='Vehicle Plate / የተሽከርካሪ ሰሌዳ')
    reason_for_entry = fields.Char(string='Reason for Entry / የገባበት ምክንያት')
