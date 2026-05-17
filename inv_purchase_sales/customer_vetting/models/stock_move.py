# -*- coding: utf-8 -*-
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_in_move_lines(self):
        self.ensure_one()
        if (
            self.picking_id
            and self.picking_id._customer_vetting_is_product_detail_so_receipt()
        ):
            return self.env['stock.move.line']
        return super()._get_in_move_lines()
