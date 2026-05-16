from odoo import models, fields


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    exchange_rate_bank_id = fields.Many2one(
        'res.bank',
        string='Exchange Rate Bank',
        help='Bank associated with this exchange rate line.'
    )
