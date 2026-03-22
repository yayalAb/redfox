# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    grn_gross_weight = fields.Float(
        string='Gross Weight / ጠቅላላ ክብደት',
        digits=(16, 2)
    )
    grn_tare_weight = fields.Float(
        string='Tare Weight / ነጠላ ክብደት',
        digits=(16, 2)
    )
    grn_bag_count = fields.Integer(
        string='No. of Bags / የጆንያው ብዛት'
    )
    grn_quality_pct = fields.Float(
        string='Quality % / የማጣሪያ ጥራት%',
        digits=(5, 2)
    )
    grn_net_weight = fields.Float(
        string='Net Weight / የተጣራ ክብደት',
        compute='_compute_grn_net_weight',
        store=True,
        digits=(16, 2)
    )

    @api.depends('grn_gross_weight', 'grn_tare_weight')
    def _compute_grn_net_weight(self):
        for rec in self:
            rec.grn_net_weight = rec.grn_gross_weight - rec.grn_tare_weight
