# -*- coding: utf-8 -*-

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_withholding_tax_threshold(self):
        """Get the withholding tax threshold from config (default 20000)."""
        return float(
            self.env['ir.config_parameter'].sudo().get_param(
                'withholding_tax_threshold.amount_threshold', '20000.0'
            )
        )

    def _is_withholding_tax(self, tax):
        """Identify if a tax is a withholding tax (negative or withhold in name/group)."""
        if not tax:
            return False
        if tax.amount < 0:
            return True
        name = (tax.name or '').lower()
        if 'withhold' in name or 'withholding' in name or 'retention' in name:
            return True
        if tax.tax_group_id and tax.tax_group_id.preceding_subtotal:
            group_label = (tax.tax_group_id.preceding_subtotal or '').lower()
            if 'withhold' in group_label or 'withholding' in group_label:
                return True
        return False

    def _apply_withholding_tax_threshold(self):
        """
        Apply withholding tax only when amount_untaxed (before tax total) > threshold.
        Remove withholding from all lines when amount_untaxed <= threshold.
        Works for Purchase Quotations (RFQ) and Purchase Orders.
        """
        self.ensure_one()
        if self.state == 'cancel':
            return

        threshold = self._get_withholding_tax_threshold()
        self.flush_recordset(['amount_untaxed'])
        amount_untaxed = abs(self.amount_untaxed or 0.0)

        order_lines = self.order_line
        if not order_lines:
            return

        for line in order_lines:
            if not line.taxes_id:
                continue

            if amount_untaxed <= threshold:
                withholding_taxes = line.taxes_id.filtered(
                    lambda t: self._is_withholding_tax(t)
                )
                if withholding_taxes:
                    line.taxes_id = line.taxes_id - withholding_taxes
            else:
                if line.product_id:
                    default_taxes = line.product_id.supplier_taxes_id
                    withholding_from_product = default_taxes.filtered(
                        lambda t: self._is_withholding_tax(t)
                    )
                    if withholding_from_product and withholding_from_product not in line.taxes_id:
                        line.taxes_id = line.taxes_id | withholding_from_product

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            order._apply_withholding_tax_threshold()
        return orders

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get('skip_withholding_tax_threshold'):
            for order in self:
                order._apply_withholding_tax_threshold()
        return result

    @api.onchange('order_line', 'order_line.product_qty', 'order_line.price_unit',
                  'order_line.discount', 'order_line.taxes_id')
    def _onchange_order_line_withholding_threshold(self):
        """Update withholding taxes in real-time when amounts change in form."""
        if self.state == 'cancel':
            return

        threshold = self._get_withholding_tax_threshold()
        amount_untaxed = sum(
            line.price_subtotal for line in self.order_line
        )

        for line in self.order_line:
            if not line.taxes_id:
                continue

            if amount_untaxed <= threshold:
                withholding_taxes = line.taxes_id.filtered(
                    lambda t: self._is_withholding_tax(t)
                )
                if withholding_taxes:
                    line.taxes_id = line.taxes_id - withholding_taxes
            else:
                if line.product_id:
                    default_taxes = line.product_id.supplier_taxes_id
                    withholding_from_product = default_taxes.filtered(
                        lambda t: self._is_withholding_tax(t)
                    )
                    if withholding_from_product and withholding_from_product not in line.taxes_id:
                        line.taxes_id = line.taxes_id | withholding_from_product
