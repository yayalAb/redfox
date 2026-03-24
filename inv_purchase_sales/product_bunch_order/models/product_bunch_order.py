from odoo import fields, models


class ProductBunchOrder(models.Model):
    _name = 'product.bunch.order'
    _description = 'Product Bunch Order'

    name = fields.Char(string='Name', required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
    )
    line_ids = fields.One2many(
        'product.bunch.order.line',
        'bunch_order_id',
        string='Product Lines'
    )


class ProductBunchOrderLine(models.Model):
    _name = 'product.bunch.order.line'
    _description = 'Product Bunch Order Line'

    bunch_order_id = fields.Many2one(
        'product.bunch.order',
        string='Bunch Order',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
