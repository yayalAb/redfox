# -*- coding: utf-8 -*-
from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    lc_letter_id = fields.Many2one(
        'lc.letter',
        string='LC Letter',
        help='Letter of Credit reference',
    )
