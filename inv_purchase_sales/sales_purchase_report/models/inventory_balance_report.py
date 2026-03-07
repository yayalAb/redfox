from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression

class InventoryStockBalanceReport(models.TransientModel):
    _name = "sale.report.tree"
    _description = "Sales Report"

    sale_id = fields.Many2one('sale.order', string="Article Code")
    product_id = fields.Many2one('product.template', string="Product")
    category_id = fields.Many2one('product.category', string="Category")
    sub_category_id = fields.Many2one('product.category', string="Sub Category")
    quantity = fields.Float( string="Quantity")
    avg_amount = fields.Float( string="Price")
    price_tax = fields.Float( string="TAX")
    total_amount = fields.Float(string="Total Price")


class PurchaseReport(models.TransientModel):
    _name = "purchase.report.tree"
    _description = "Purchase Report Tree"
    sale_id = fields.Many2one('purchase.order', string="Article Code")
    product_id = fields.Many2one('product.template', string="Product")
    category_id = fields.Many2one('product.category', string="Category")
    sub_category_id = fields.Many2one('product.category', string="Sub Category")
    quantity = fields.Float(string="Quantity")
    avg_amount = fields.Float(string="Price")
    price_tax = fields.Float(string="TAX")
    total_amount = fields.Float(string="Total Price")



