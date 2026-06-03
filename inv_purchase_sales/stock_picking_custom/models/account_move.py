from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    fs_no = fields.Char(string='FS No')
    mrc_no = fields.Char(string='MRC No')
    payment_method = fields.Selection(
        selection=[
            ('cash', 'Cash'),
            ('credit', 'Credit'),
        ],
        string='Method',
    )

    def refresh_invoice_currency_rate(self):
        """Support legacy invoice form buttons from Studio or older customizations."""
        self._compute_invoice_currency_rate()
        self.line_ids._compute_currency_rate()
        return True
