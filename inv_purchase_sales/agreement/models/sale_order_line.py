# © 2017 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""
Odoo 18 sale order views may reference translated_product_name on order lines
without defining the field on all installations. Declaring it here keeps view
validation working when upgrading the agreement module.
"""
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    translated_product_name = fields.Text(
        compute="_compute_translated_product_name",
    )

    @api.depends("product_id", "order_id.partner_id")
    def _compute_translated_product_name(self):
        for line in self:
            if not line.product_id:
                line.translated_product_name = False
                continue
            lang = line.order_id._get_lang() if line.order_id else False
            line.translated_product_name = line.product_id.with_context(
                lang=lang,
            ).display_name
