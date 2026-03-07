from odoo import models, api, _, fields
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.constrains('product_qty', 'price_unit')
    def _check_quantity_and_price_not_negative(self):
        """
        Validates that the ordered quantity and unit price on a purchase order line
        are not negative. Zero is allowed for both fields.
        """
        for line in self:
            if line.product_qty < 0:
                raise ValidationError(_(
                    "The ordered quantity for product [%s] cannot be negative.",
                    line.product_id.display_name
                ))
            if line.price_unit < 0:
                raise ValidationError(_(
                    "The unit price for product [%s] cannot be negative.",
                    line.product_id.display_name
                ))