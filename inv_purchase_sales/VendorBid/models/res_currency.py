from odoo import api, fields, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company=None, date=None):
        if from_currency == to_currency:
            return 1
        company = company or self.env.company
        date = date or fields.Date.context_today(self)
        bank_id = self.env.context.get('exchange_rate_bank_id')
        ctx = {
            'to_currency': to_currency.id,
            'date': str(date),
        }
        if bank_id:
            ctx['exchange_rate_bank_id'] = bank_id
        return from_currency.with_company(company).with_context(**ctx).inverse_rate

    def _get_rates(self, company, date):
        if not self.ids:
            return {}
        bank_id = self.env.context.get('exchange_rate_bank_id')
        if not bank_id:
            return super()._get_rates(company, date)
        company = company or self.env.company
        root = company.root_id
        Rate = self.env['res.currency.rate'].sudo()
        result = {}
        for currency in self:
            line = Rate.search(
                [
                    ('currency_id', '=', currency.id),
                    ('name', '<=', date),
                    ('company_id', 'in', (False, root.id)),
                    ('exchange_rate_bank_id', '=', bank_id),
                ],
                order='company_id desc, name desc',
                limit=1,
            )
            if not line:
                line = Rate.search(
                    [
                        ('currency_id', '=', currency.id),
                        ('name', '<=', date),
                        ('company_id', 'in', (False, root.id)),
                        ('exchange_rate_bank_id', '=', False),
                    ],
                    order='company_id desc, name desc',
                    limit=1,
                )
            if not line:
                sub = currency.with_context(exchange_rate_bank_id=False)._get_rates(
                    company, date
                )
                result[currency.id] = sub.get(currency.id, 1.0)
            else:
                result[currency.id] = line.rate or 1.0
        return result
