# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    customer_vetting_mrp_production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing order (customer vetting)',
        ondelete='set null',
        copy=False,
        index=True,
    )
    customer_vetting_is_raw_receipt_line = fields.Boolean(
        compute='_compute_customer_vetting_is_raw_receipt_line',
    )

    def _customer_vetting_raw_moves_same_picking(self):
        """Incoming customer-vetting receipt moves that are raw-product (other) lines."""
        picking = self.picking_id
        if not picking or picking.picking_type_id.code != 'incoming':
            return self.env['stock.move']
        if not picking._customer_vetting_is_product_detail_so_receipt():
            return self.env['stock.move']
        order = picking._customer_vetting_product_detail_receipt_sale_order()
        if not order:
            return self.env['stock.move']
        raw_products = order.vetting_detail_line_ids.filtered(
            lambda l: l.detail_type == 'other'
            and l.product_id
            and l.product_id.is_storable
        ).mapped('product_id')
        if not raw_products:
            return self.env['stock.move']
        return picking.move_ids.filtered(lambda m: m.product_id in raw_products)

    @api.depends(
        'picking_id',
        'picking_id.move_ids',
        'picking_id.move_ids.product_id',
        'picking_id.customer_vetting_sale_id',
        'picking_id.customer_vetting_sale_id.vetting_detail_line_ids',
        'picking_id.customer_vetting_sale_id.vetting_detail_line_ids.detail_type',
        'picking_id.customer_vetting_sale_id.vetting_detail_line_ids.product_id',
        'product_id',
    )
    def _compute_customer_vetting_is_raw_receipt_line(self):
        for move in self:
            picking = move.picking_id
            if (
                not picking
                or picking.picking_type_id.code != 'incoming'
                or not picking._customer_vetting_is_product_detail_so_receipt()
            ):
                move.customer_vetting_is_raw_receipt_line = False
                continue
            raw_moves = move._customer_vetting_raw_moves_same_picking()
            move.customer_vetting_is_raw_receipt_line = move in raw_moves

    def _customer_vetting_skip_valuation(self):
        """Skip stock valuation for vetting receipts, MO produce, and MO deliveries."""
        self.ensure_one()
        if self.env.context.get('customer_vetting_skip_valuation'):
            return True
        picking = self.picking_id
        if picking and picking.customer_vetting_mrp_production_id:
            return True
        if (
            picking
            and picking.picking_type_id.code == 'incoming'
            and picking._customer_vetting_is_product_detail_so_receipt()
        ):
            return True
        mo = self.production_id
        if mo and mo.customer_vetting_receipt_picking_id:
            return True
        return False

    def _get_in_move_lines(self):
        self.ensure_one()
        if self._customer_vetting_skip_valuation():
            return self.env['stock.move.line']
        return super()._get_in_move_lines()

    def _get_out_move_lines(self):
        self.ensure_one()
        if self._customer_vetting_skip_valuation():
            return self.env['stock.move.line']
        return super()._get_out_move_lines()

    def _should_exclude_for_valuation(self):
        if self._customer_vetting_skip_valuation():
            return True
        return super()._should_exclude_for_valuation()

    def _create_in_svl(self, forced_quantity=None):
        moves = self.filtered(lambda m: not m._customer_vetting_skip_valuation())
        if not moves:
            return self.env['stock.valuation.layer']
        return super(StockMove, moves)._create_in_svl(forced_quantity)

    def _create_out_svl(self, forced_quantity=None):
        moves = self.filtered(lambda m: not m._customer_vetting_skip_valuation())
        if not moves:
            return self.env['stock.valuation.layer']
        return super(StockMove, moves)._create_out_svl(forced_quantity)
