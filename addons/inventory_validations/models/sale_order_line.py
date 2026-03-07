from odoo import models, api, _, fields
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_uom_qty', 'price_unit')
    def _check_quantity_and_price_not_negative(self):
        """
        Validates that the ordered quantity and unit price on a sales order line
        are not negative. Zero is allowed for both fields.
        """
        for line in self:
            if line.product_uom_qty < 0:
                raise ValidationError(_(
                    "The ordered quantity for product [%s] cannot be negative.",
                    line.product_id.display_name
                ))
            if line.price_unit < 0:
                raise ValidationError(_(
                    "The unit price for product [%s] cannot be negative.",
                    line.product_id.display_name
                ))