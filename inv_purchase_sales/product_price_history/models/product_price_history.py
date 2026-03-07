from odoo import models, fields

class ProductPriceHistory(models.Model):
    _name = 'product.price.history'
    _description = 'Product Sales Price History'
    _order = 'change_date desc'

    product_template_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        ondelete='cascade' # If the product is deleted, delete its history
    )
    price = fields.Monetary(
        string='Price',
        required=True
    )
    currency_id = fields.Many2one(
        related='product_template_id.currency_id',
        string='Currency'
    )
    change_date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
        readonly=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Changed By',
        default=lambda self: self.env.user,
        readonly=True
    )