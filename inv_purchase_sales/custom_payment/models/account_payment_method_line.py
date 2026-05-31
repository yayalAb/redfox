# -*- coding: utf-8 -*-
from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountPaymentMethodLine(models.Model):
    _inherit = 'account.payment.method.line'

    @api.constrains('payment_method_id', 'journal_id')
    def _check_unique_payment_method_per_journal(self):
        for line in self:
            if not line.payment_method_id or not line.journal_id:
                continue
            duplicate = self.search([
                ('id', '!=', line.id),
                ('journal_id', '=', line.journal_id.id),
                ('payment_method_id', '=', line.payment_method_id.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    'Payment method "%(method)s" is already configured on journal "%(journal)s".',
                    method=line.payment_method_id.display_name,
                    journal=line.journal_id.display_name,
                ))
