from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    price_history_ids = fields.One2many(
        'product.price.history',
        'product_template_id',
        string='Price History',
        readonly=True
    )

    def write(self, vals):
        """
        Override the write method to intercept changes to the sales price.
        """
        # We only care if the 'list_price' is being changed.
        if 'list_price' in vals:
            # The 'write' method can be called on multiple records at once, so we loop.
            for product in self:
                # Check if the new price is actually different from the old one.
                if product.list_price != vals['list_price']:
                    # Create a new history record with the OLD price.
                    self.env['product.price.history'].create({
                        'product_template_id': product.id,
                        'price': product.list_price, # The old price before the save
                    })
        
        # After our logic, call the original write method to save the changes.
        return super(ProductTemplate, self).write(vals)