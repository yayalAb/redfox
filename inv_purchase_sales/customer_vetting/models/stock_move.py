# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import float_is_zero, float_round


class StockMove(models.Model):
    _inherit = 'stock.move'

    customer_vetting_line_total_weight = fields.Float(
        string='Total Weight',
        compute='_compute_customer_vetting_line_weight_display',
        digits='Stock Weight',
    )
    customer_vetting_line_net_weight = fields.Float(
        string='Net Weight',
        compute='_compute_customer_vetting_line_weight_display',
        digits='Stock Weight',
    )
    customer_vetting_line_p_net_weight = fields.Float(
        string='P. Net Weight',
        compute='_compute_customer_vetting_line_weight_display',
        digits='Stock Weight',
        help='Proportional net weight for this line (raw lines share weighbridge net by demand qty).',
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

    @api.depends(
        'picking_id',
        'picking_id.customer_vetting_gross_weight',
        'picking_id.customer_vetting_tare_weight',
        'picking_id.move_ids',
        'picking_id.move_ids.product_uom_qty',
        'picking_id.move_ids.product_id',
        'picking_id.customer_vetting_sale_id',
        'picking_id.customer_vetting_sale_id.vetting_detail_line_ids',
        'picking_id.customer_vetting_sale_id.vetting_detail_line_ids.detail_type',
        'picking_id.customer_vetting_sale_id.vetting_detail_line_ids.product_id',
        'product_uom_qty',
        'product_id',
    )
    def _compute_customer_vetting_line_weight_display(self):
        for move in self:
            picking = move.picking_id
            if (
                not picking
                or picking.picking_type_id.code != 'incoming'
                or not picking._customer_vetting_is_product_detail_so_receipt()
            ):
                move.customer_vetting_line_total_weight = 0.0
                move.customer_vetting_line_net_weight = 0.0
                move.customer_vetting_line_p_net_weight = 0.0
                continue
            raw_moves = move._customer_vetting_raw_moves_same_picking()
            if move not in raw_moves:
                move.customer_vetting_line_total_weight = 0.0
                move.customer_vetting_line_net_weight = 0.0
                move.customer_vetting_line_p_net_weight = 0.0
                continue
            gross = picking.customer_vetting_gross_weight or 0.0
            tare = picking.customer_vetting_tare_weight or 0.0
            net = gross - tare
            if net < 0:
                net = 0.0
            move.customer_vetting_line_total_weight = gross
            move.customer_vetting_line_net_weight = net
            total_qty = sum(raw_moves.mapped('product_uom_qty'))
            if float_is_zero(total_qty, precision_rounding=1e-6):
                move.customer_vetting_line_p_net_weight = 0.0
            else:
                share = move.product_uom_qty / total_qty
                p_net = net * share
                prec = self.env['decimal.precision'].precision_get('Stock Weight')
                move.customer_vetting_line_p_net_weight = float_round(
                    p_net, precision_digits=prec
                )

    def _get_in_move_lines(self):
        self.ensure_one()
        if (
            self.picking_id
            and self.picking_id._customer_vetting_is_product_detail_so_receipt()
        ):
            return self.env['stock.move.line']
        return super()._get_in_move_lines()
