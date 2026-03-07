from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hs_code = fields.Char(
        string="HS Code",
        help="Harmonized System Code for customs declaration."
    )
  