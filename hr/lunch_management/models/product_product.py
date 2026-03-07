from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_meal = fields.Boolean(string="Is Meal")

class productTemplate(models.Model):
    _inherit = 'product.template'

    is_meal = fields.Boolean(string="Is Meal")