from odoo import models, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('list_price', 'standard_price')
    def _check_prices_not_negative(self):
        """
        Validatesthat the sales price and cost of a product are not negative.
        """
        for product in self:
            if product.list_price < 0:
                raise ValidationError(_('The Sales Price cannot be negative.'))
            if product.standard_price < 0:
                raise ValidationError(_('The Cost price cannot be negative.'))