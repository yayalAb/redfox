# Copyright 2015-2016 Akretion (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ProductCategory(models.Model):
    _inherit = "product.category"

    allow_negative_stock = fields.Boolean(
        help="Allow negative stock levels for the stockable products "
        "attached to this category. The options doesn't apply to products "
        "attached to sub-categories of this category.",
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    allow_negative_stock = fields.Boolean(
        help="If this option is not active on this product nor on its "
        "product category and that this product is a stockable product, "
        "then the validation of the related stock moves will be blocked if "
        "the stock level becomes negative with the stock move.",
    )

    @api.constrains("list_price")
    def validate_name_description(self):
        for product in self:
            if product.list_price < 0:
                raise ValidationError(
                    _("sale price cannot be negative"))

    @api.constrains("standard_price")
    def validate_standard_price(self):
        for product in self:
            if product.standard_price < 0:
                raise ValidationError(
                    _("cost cannot be negative"))
