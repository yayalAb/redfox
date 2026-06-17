# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_origin = fields.Selection(
        [('local', 'Local'), ('foreign', 'Foreign')],
        string='Purchase Type',
    )
    x_payment_term_foreign = fields.Selection(
        selection=[
            ('lc', 'LC'),
            ('tt', 'TT'),
            ('cad', 'CAD'),
        ],
        string='Payment Method',
        tracking=True,
    )
    lc_letter_id = fields.Many2one(
        'lc.letter',
        string='Foreign Payment Term',
        help='Linked foreign payment term document (LC, CAD, or TT)',
    )

    @api.onchange('x_payment_term_foreign')
    def _onchange_x_payment_term_foreign_lc_letter(self):
        if self.lc_letter_id and self.x_payment_term_foreign:
            if self.lc_letter_id.payment_instrument != self.x_payment_term_foreign:
                self.lc_letter_id = False

    @api.onchange('lc_letter_id')
    def _onchange_lc_letter_id_payment_term(self):
        if self.lc_letter_id and not self.x_payment_term_foreign:
            self.x_payment_term_foreign = self.lc_letter_id.payment_instrument
