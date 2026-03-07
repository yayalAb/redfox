from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bincard_no = fields.Char(
        'Card No.',
        copy=False,
        help="Unique Card Number for the Bin Card report."
    )

    _sql_constraints = [
        (
            'default_code_unique',
            'UNIQUE(default_code)',
            'The Item Code must be unique across all products!'
        ),
        (
            'bincard_no_unique',
            'UNIQUE(bincard_no)',
            'The Card No. must be unique across all products!'
        ),
    ]