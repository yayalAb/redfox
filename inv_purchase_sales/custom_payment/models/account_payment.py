# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    maturity_date = fields.Date(
        string='Maturity Date',
        tracking=True,
        help='Due date used on payment journal items when set.',
    )
    check_transfer_no = fields.Char(
        string='Check/Transfer No',
        required=True,
        copy=False,
        tracking=True,
        help='Cheque number, bank transfer reference, or other payment instrument number.',
    )

    _sql_constraints = [
        (
            'check_transfer_no_unique',
            'UNIQUE(check_transfer_no)',
            'Check/Transfer number must be unique.',
        ),
    ]

    @api.constrains('check_transfer_no')
    def _check_check_transfer_no(self):
        for payment in self:
            if not (payment.check_transfer_no or '').strip():
                raise ValidationError(
                    _('Check/Transfer number is required.')
                )

    @api.depends('payment_method_code', 'journal_id.type')
    def _compute_show_require_partner_bank(self):
        super()._compute_show_require_partner_bank()
        for payment in self:
            payment.show_partner_bank_account = True

    @api.onchange('date')
    def _onchange_date_set_maturity_date(self):
        if not self.maturity_date:
            self.maturity_date = self.date

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        line_vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals,
            force_balance=force_balance,
        )
        maturity = self.maturity_date or self.date
        for vals in line_vals_list:
            if 'date_maturity' in vals:
                vals['date_maturity'] = maturity
        return line_vals_list
