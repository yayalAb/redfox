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
