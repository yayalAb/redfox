# -*- coding: utf-8 -*-

from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

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
        # Negative amount = withholding (retention) tax
        if tax.amount < 0:
            return True
        name = (tax.name or '').lower()
        if 'withhold' in name or 'withholding' in name or 'retention' in name:
            return True
        # Check tax group preceding_subtotal (e.g. "Tax withholding")
        if tax.tax_group_id and tax.tax_group_id.preceding_subtotal:
            group_label = (tax.tax_group_id.preceding_subtotal or '').lower()
            if 'withhold' in group_label or 'withholding' in group_label:
                return True
        return False

    def _apply_withholding_tax_threshold(self):
        """
        Apply withholding tax only when amount_untaxed (before tax total) > threshold.
        Remove withholding from all lines when amount_untaxed <= threshold.
        """
        self.ensure_one()
        if not self.is_invoice(True) or self.state != 'draft':
            return

        threshold = self._get_withholding_tax_threshold()
        # Use amount_untaxed (total before tax) - ensure it's computed
        self.flush_recordset(['amount_untaxed'])
        amount_untaxed = abs(self.amount_untaxed)

        invoice_lines = self.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product'
        )
        if not invoice_lines:
            return

        for line in invoice_lines:
            if not line.tax_ids:
                continue

            if amount_untaxed <= threshold:
                # Remove withholding taxes when below threshold
                withholding_taxes = line.tax_ids.filtered(
                    lambda t: self._is_withholding_tax(t)
                )
                if withholding_taxes:
                    new_tax_ids = line.tax_ids - withholding_taxes
                    line.tax_ids = new_tax_ids
            else:
                # Above threshold: ensure withholding is applied if in product defaults
                # Get product default taxes (supplier_taxes_id for bills, taxes_id for sales)
                if line.product_id:
                    if self.move_type in ('in_invoice', 'in_refund', 'in_receipt'):
                        default_taxes = line.product_id.supplier_taxes_id
                    else:
                        default_taxes = line.product_id.taxes_id
                    withholding_from_product = default_taxes.filtered(
                        lambda t: self._is_withholding_tax(t)
                    )
                    if withholding_from_product and withholding_from_product not in line.tax_ids:
                        line.tax_ids = line.tax_ids | withholding_from_product

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            move._apply_withholding_tax_threshold()
        return moves

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get('skip_withholding_tax_threshold'):
            for move in self:
                move._apply_withholding_tax_threshold()
        return result

    @api.onchange('invoice_line_ids', 'invoice_line_ids.quantity', 'invoice_line_ids.price_unit',
                  'invoice_line_ids.discount', 'invoice_line_ids.tax_ids')
    def _onchange_invoice_line_ids_withholding_threshold(self):
        """Update withholding taxes in real-time when amounts change in form."""
        if not self.is_invoice(True) or self.state != 'draft':
            return

        threshold = self._get_withholding_tax_threshold()
        # Compute amount_untaxed from current line values (use price_subtotal when available)
        amount_untaxed = sum(
            line.price_subtotal for line in self.invoice_line_ids
            if line.display_type == 'product'
        )

        for line in self.invoice_line_ids:
            if line.display_type != 'product' or not line.tax_ids:
                continue

            if amount_untaxed <= threshold:
                withholding_taxes = line.tax_ids.filtered(
                    lambda t: self._is_withholding_tax(t)
                )
                if withholding_taxes:
                    line.tax_ids = line.tax_ids - withholding_taxes
            else:
                if line.product_id:
                    if self.move_type in ('in_invoice', 'in_refund', 'in_receipt'):
                        default_taxes = line.product_id.supplier_taxes_id
                    else:
                        default_taxes = line.product_id.taxes_id
                    withholding_from_product = default_taxes.filtered(
                        lambda t: self._is_withholding_tax(t)
                    )
                    if withholding_from_product and withholding_from_product not in line.tax_ids:
                        line.tax_ids = line.tax_ids | withholding_from_product
