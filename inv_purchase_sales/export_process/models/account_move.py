# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    export_order_id = fields.Many2one('export.export.order', string='Export Order', copy=False)
