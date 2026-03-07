from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    agreement_id = fields.Many2one(
        "sale.agreement",
        string="Agreement",
        readonly=True,
    )