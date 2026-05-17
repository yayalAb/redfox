# -*- coding: utf-8 -*-
"""
Sale order line: translated_product_name is referenced in sale views / reports on
Odoo 18.0, but some builds ship views without the model field. Defining it here
unblocks view validation. Remove this file if your ``sale`` module already
declares the same field (duplicate field error on upgrade).
"""
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    translated_product_name = fields.Text(compute='_compute_translated_product_name')

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_translated_product_name(self):
        for line in self:
            if not line.product_id:
                line.translated_product_name = False
                continue
            lang = line.order_id._get_lang() if line.order_id else False
            line.translated_product_name = line.product_id.with_context(
                lang=lang,
            ).display_name
