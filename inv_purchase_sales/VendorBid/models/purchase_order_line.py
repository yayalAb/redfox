from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    rfp_id = fields.Many2one('supplies.rfp', string='RFP', index=True, copy=False)

    recommended = fields.Boolean(string='Recommended', default=False)
    out_of_stock = fields.Selection([
        ('out_of_stock', 'Out of Stock'),
        ('out_of_specification', 'Out of Specification')
    ], string='Status', default=False)
    tax_included_price = fields.Float(
        string='Tax Included Price',
        digits='Product Price',
        help='Enter the price including taxes. Unit price will be calculated automatically.'
    )
    hs_code = fields.Char(string='HS Code')

    @api.onchange('out_of_stock')
    def _onchange_out_of_stock(self):
        """Clear price when out of stock status is selected"""
        if self.out_of_stock:
            self.price_unit = 0.0
    
    @api.model_create_multi
    def create(self, vals_list):
        """Apply taxes from order when creating new lines"""
        lines = super().create(vals_list)
        for line in lines:
            if line.order_id.applied_tax_ids:
                line.taxes_id = line.order_id.applied_tax_ids
        return lines
    
    @api.onchange('product_id')
    def _onchange_product_id_apply_taxes(self):
        """Apply taxes from order when product is selected, after parent onchange"""
        # Let parent onchange run first (it will be called automatically)
        # Then override taxes if order has applied_tax_ids
        if self.order_id and self.order_id.applied_tax_ids:
            # Apply taxes from order after product is selected
            self.taxes_id = self.order_id.applied_tax_ids
    
    @api.onchange('product_qty')
    def _onchange_product_qty_preserve_price(self):
        """Preserve unit price when quantity changes"""
        # Get the original price_unit value before any onchange modifications
        # Use _origin if available (for existing records), otherwise use current value
        original_price = getattr(self._origin, 'price_unit', None) if hasattr(self, '_origin') and self._origin else self.price_unit
        
        # If price_unit was set to 0 incorrectly, restore it
        if self.price_unit == 0.0 and not self.out_of_stock:
            # If we have tax_included_price, recalculate from it
            if self.tax_included_price and self.order_id and self.order_id.price_tax_included:
                self._onchange_tax_included_price()
            # Otherwise, restore the original price if it was valid
            elif original_price and original_price > 0:
                self.price_unit = original_price
    
    @api.onchange('tax_included_price')
    def _onchange_tax_included_price(self):
        """Calculate unit price from tax included price"""
        if self.tax_included_price and self.order_id and self.order_id.price_tax_included:
            if self.taxes_id:
                # Reverse calculate: get base price from tax-included price
                # First, compute taxes on a base of 1 to understand the tax structure
                base_price = 1.0
                tax_result = self.taxes_id.compute_all(
                    base_price,
                    currency=self.order_id.currency_id,
                    quantity=1.0,
                    product=self.product_id,
                    partner=self.order_id.partner_id
                )
                
                if tax_result and 'total_included' in tax_result:
                    # Calculate the multiplier (how much tax adds to base price)
                    tax_multiplier = tax_result['total_included'] / tax_result['total_excluded']
                    # Reverse: divide tax-included price by multiplier to get base price
                    self.price_unit = self.tax_included_price / tax_multiplier
                else:
                    # Fallback calculation for simple percentage taxes
                    total_tax_rate = sum(self.taxes_id.mapped('amount')) / 100.0
                    self.price_unit = self.tax_included_price / (1 + total_tax_rate)
            else:
                # No taxes, so tax included price equals unit price
                self.price_unit = self.tax_included_price

    def write(self, vals):
        """Ensure price_unit is 0 when out_of_stock is set"""
        result = super().write(vals)
        if 'out_of_stock' in vals and vals.get('out_of_stock'):
            for line in self:
                if line.out_of_stock:
                    line.price_unit = 0.0
        return result