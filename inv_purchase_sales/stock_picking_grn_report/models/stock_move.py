# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    grn_gross_weight = fields.Float(string='Total Weight (GRN)')
    grn_tare_weight = fields.Float(string='Unit / Tare Weight (GRN)')
    grn_bag_count = fields.Integer(string='Bag Count')
    grn_quality_pct = fields.Float(string='Cleaning Quality %')
    grn_net_weight = fields.Float(
        string='Net Weight (GRN)',
        compute='_compute_grn_net_weight',
        store=True,
    )

    @api.depends('grn_gross_weight', 'grn_tare_weight')
    def _compute_grn_net_weight(self):
        for rec in self:
            rec.grn_net_weight = (rec.grn_gross_weight or 0.0) - (rec.grn_tare_weight or 0.0)
