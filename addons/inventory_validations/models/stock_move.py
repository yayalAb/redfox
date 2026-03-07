from odoo import models, api, _, fields
from odoo.exceptions import ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'

    # As seen in the form XML, the editable "Quantity" in the Operations tab
    # is the 'quantity' field on the 'stock.move' model.
    @api.constrains('quantity')
    def _check_done_quantity_not_negative(self):
        """
        Validates that the 'Done' quantity on a stock move is not negative.
        """
        for move in self:
            if move.quantity < 0:
                # Adding the product name to the error makes it more user-friendly.
                raise ValidationError(_(
                    "The processed quantity for product [%s] cannot be negative.",
                    move.product_id.display_name
                ))