# -*- coding: utf-8 -*-
from odoo import models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_print_payment_voucher(self):
        """Print payment voucher report"""
        self.ensure_one()
        return self.env.ref('payment_voucher_template.action_report_payment_voucher').report_action(self)

