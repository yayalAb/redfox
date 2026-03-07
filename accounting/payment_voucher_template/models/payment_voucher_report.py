# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.tools.misc import formatLang


class PaymentVoucherReport(models.AbstractModel):
    _name = 'report.payment_voucher_template.payment_voucher_document'
    _description = 'Payment Voucher Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        payments = self.env['account.payment'].browse(docids)
        
        # Helper function to convert amount to words
        def amount_to_words(amount, currency):
            try:
                if hasattr(currency, 'amount_to_text'):
                    return currency.amount_to_text(amount)
                else:
                    # Fallback: simple conversion
                    return formatLang(self.env, amount, currency_obj=currency)
            except:
                return str(amount)
        
        # Get allocation lines from payment move
        def get_allocation_lines(payment):
            lines = []
            if payment.move_id:
                for line in payment.move_id.line_ids:
                    if line.account_id and (line.debit > 0 or line.credit > 0):
                        lines.append({
                            'account': line.account_id.code or '',
                            'account_name': line.account_id.name or '',
                            'debit': line.debit,
                            'credit': line.credit,
                        })
            return lines
        
        # Get cheque number safely
        def get_cheque_number(payment):
            """Get cheque number from payment, checking various possible fields"""
            if hasattr(payment, 'check_number') and payment.check_number:
                return payment.check_number
            elif hasattr(payment, 'cheque_reference') and payment.cheque_reference:
                return payment.cheque_reference
            elif payment.payment_reference:
                return payment.payment_reference
            return ''
        
        return {
            'doc_ids': docids,
            'doc_model': 'account.payment',
            'docs': payments,
            'amount_to_words': amount_to_words,
            'get_allocation_lines': get_allocation_lines,
            'get_cheque_number': get_cheque_number,
        }

