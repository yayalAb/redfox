# -*- coding: utf-8 -*-
"""
Sale order line: translated_product_name is referenced in sale views / reports on
Odoo 18.0, but some builds ship views without the model field. Defining it here
unblocks view validation. Remove this file if your ``sale`` module already
declares the same field (duplicate field error on upgrade).
"""
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    translated_product_name = fields.Text(
        compute='_compute_translated_product_name')

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._customer_vetting_sync_order_details()
        return lines

    def write(self, vals):
        orders_before = self.mapped('order_id')
        res = super().write(vals)
        if self.env.context.get('customer_vetting_skip_detail_reconcile'):
            return res
        # orders_after = self.mapped('order_id')
        # (orders_before | orders_after)._customer_vetting_sync_order_details()
        return res

    def unlink(self):
        orders = self.mapped('order_id')
        res = super().unlink()
        if not self.env.context.get('customer_vetting_skip_detail_reconcile'):
            orders._customer_vetting_sync_order_details()
        return res

    def _customer_vetting_sync_order_details(self):
        self.mapped('order_id').filtered(
            'service_request_id')._sync_service_vetting_detail_lines()

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_translated_product_name(self):
        for line in self:
            if not line.product_id:
                line.translated_product_name = False
                continue
            lang = line.order_id._get_lang() if line.order_id else False
            line.translated_product_name = line.product_id.with_context(
                lang=lang,
            ).display_name
