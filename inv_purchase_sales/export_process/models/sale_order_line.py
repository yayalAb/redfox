# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Referenced by sale order form views on Odoo 18; define if missing from sale/custom addons.
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
