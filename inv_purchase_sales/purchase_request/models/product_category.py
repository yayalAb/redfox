from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = 'product.category'

    reference_code = fields.Char(string='Reference Code', help='A unique reference code for the product category.')
    