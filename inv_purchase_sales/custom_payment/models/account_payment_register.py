# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    maturity_date = fields.Date(
        string='Maturity Date',
        help='Due date stored on the created payment.',
    )
    check_transfer_no = fields.Char(
        string='Check/Transfer No',
        required=True,
        help='Cheque number, bank transfer reference, or other payment instrument number.',
    )

    @api.depends('payment_method_line_id.code')
    def _compute_show_require_partner_bank(self):
        super()._compute_show_require_partner_bank()
        for wizard in self:
            wizard.show_partner_bank_account = True

    @api.onchange('payment_date')
    def _onchange_payment_date_set_maturity_date(self):
        if not self.maturity_date:
            self.maturity_date = self.payment_date

    def _apply_custom_payment_vals(self, payment_vals):
        if self.maturity_date:
            payment_vals['maturity_date'] = self.maturity_date
        payment_vals['check_transfer_no'] = self.check_transfer_no
        return payment_vals

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        return self._apply_custom_payment_vals(payment_vals)

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        return self._apply_custom_payment_vals(payment_vals)
