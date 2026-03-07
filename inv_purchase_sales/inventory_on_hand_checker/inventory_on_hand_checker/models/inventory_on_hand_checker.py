from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.constrains('quantity')
    def _check_positive_quantity(self):
        for quant in self:
            # We only want to check physical, internal locations.
            # Virtual locations like 'Inventory adjustment' are allowed to be negative.
            if quant.location_id.usage == 'internal' and quant.quantity < 0:
                raise ValidationError(_(
                    "The quantity on hand for product '%(product)s' cannot be negative in a physical location. "
                    "Location: '%(location)s'.",
                    product=quant.product_id.display_name,
                    location=quant.location_id.display_name
                ))