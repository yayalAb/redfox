# -*- coding: utf-8 -*-
import re

from odoo import api, models
from odoo.exceptions import ValidationError

_CUSTOM_PAYMENT_METHOD_CODES = frozenset({
    'cash',
    'cheque',
    'cpo',
    'tele_birr',
})

_MULTI_JOURNAL_TYPES = ('bank', 'cash', 'credit')


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        for code in _CUSTOM_PAYMENT_METHOD_CODES:
            res[code] = {'mode': 'multi', 'type': _MULTI_JOURNAL_TYPES}
        # Any user-defined method is usable on bank/cash journals.
        for method in self.sudo().search([]):
            if method.code and method.code not in res:
                res[method.code] = {'mode': 'multi', 'type': _MULTI_JOURNAL_TYPES}
        return res

    def _auto_link_payment_methods(self, payment_methods, methods_info):
        """Do not auto-add lines on every bank journal.

        Odoo's default behavior creates a line on each journal when a multi-mode
        method is created. That duplicates the line the user is already adding on
        the journal form (quick create from Incoming/Outgoing Payments).
        """
        return payment_methods

    @api.model_create_multi
    def create(self, vals_list):
        cleaned = []
        for vals in vals_list:
            vals = dict(vals)
            if vals.get('code'):
                vals['code'] = self._normalize_code(vals['code'])
            elif vals.get('name'):
                vals['code'] = self._normalize_code(vals['name'])
            cleaned.append(vals)
        return super(AccountPaymentMethod, self).create(cleaned)

    def write(self, vals):
        if vals.get('code'):
            vals = dict(vals, code=self._normalize_code(vals['code']))
        return super().write(vals)

    @api.model
    def _normalize_code(self, value):
        code = re.sub(r'[^a-z0-9_]', '_', (value or '').strip().lower())
        code = re.sub(r'_+', '_', code).strip('_')
        if not code:
            raise ValidationError(self.env._('Payment method code is required.'))
        return code
