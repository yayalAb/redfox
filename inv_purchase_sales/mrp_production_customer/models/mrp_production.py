from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        check_company=True,
        index=True,
        help='Customer this manufacturing order is produced for.',
    )
