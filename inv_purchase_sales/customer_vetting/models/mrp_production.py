# -*- coding: utf-8 -*-
from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    customer_vetting_receipt_picking_id = fields.Many2one(
        'stock.picking',
        string='Customer vetting receipt',
        ondelete='set null',
        copy=False,
        index=True,
        help='Incoming product-detail receipt validated to create this manufacturing order.',
    )
