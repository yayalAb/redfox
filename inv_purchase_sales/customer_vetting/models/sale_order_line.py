# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._customer_vetting_sync_order_details()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('customer_vetting_skip_detail_reconcile'):
            return res
        return res

    def unlink(self):
        orders = self.mapped('order_id')
        res = super().unlink()
        return res

    def _customer_vetting_sync_order_details(self):
        self.mapped('order_id').filtered(
            'service_request_id')._sync_service_vetting_detail_lines()
