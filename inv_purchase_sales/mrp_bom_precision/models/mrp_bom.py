# -*- coding: utf-8 -*-
from odoo import fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    product_qty = fields.Float(
        digits=(16, 4),
    )
    consumption = fields.Selection(
        default='flexible',
    )


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    product_qty = fields.Float(
        digits=(16, 4),
    )


class MrpBomByproduct(models.Model):
    _inherit = 'mrp.bom.byproduct'

    product_qty = fields.Float(
        digits=(16, 4),
    )
