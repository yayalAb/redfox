from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hs_code = fields.Char(string='HS Code')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    hs_code = fields.Char(related='product_tmpl_id.hs_code', string='HS Code')