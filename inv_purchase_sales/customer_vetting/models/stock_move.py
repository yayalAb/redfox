# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import float_round


class StockMove(models.Model):
    _inherit = 'stock.move'

    customer_vetting_gross_weight = fields.Float(
        string='Gross weight',
        digits='Stock Weight',
        copy=False,
    )
    customer_vetting_tare_weight = fields.Float(
        string='Tare weight',
        digits='Stock Weight',
        copy=False,
    )
    customer_vetting_line_total_weight = fields.Float(
        string='Total Weight',
        compute='_compute_customer_vetting_line_weight_display',
        digits='Stock Weight',
    )
    customer_vetting_line_net_weight = fields.Float(
        string='Net Weight',
        compute='_compute_customer_vetting_line_weight_display',
        inverse='_inverse_customer_vetting_line_net_weight',
        store=True,
        digits='Stock Weight',
    )
    customer_vetting_line_p_net_weight = fields.Float(
        string='P. Net Weight',
        compute='_compute_customer_vetting_line_weight_display',
        digits='Stock Weight',
        help='Same as net weight when gross/tare are entered per line; '
        'editing net adjusts tare (gross unchanged).',
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

    def _customer_vetting_net_weight_quantity(self):
        """Net weight (gross - tare) for this line, non-negative."""
        self.ensure_one()
        gross = self.customer_vetting_gross_weight or 0.0
        tare = self.customer_vetting_tare_weight or 0.0
        net = gross - tare
        return net if net > 0 else 0.0

    def _customer_vetting_can_sync_qty_from_line_weights(self):
        """True when demand/qty should follow net weight on an incoming receipt line."""
        self.ensure_one()
        picking = self.picking_id
        if (
            not picking
            or picking.state in ('done', 'cancel')
            or picking.picking_type_id.code != 'incoming'
            or self.state in ('done', 'cancel')
        ):
            return False
        return True

    def _customer_vetting_sync_product_uom_qty_from_line_weights(self):
        """Set demand (and open move line qty) to net weight: gross - tare."""
        for move in self:
            if not move._customer_vetting_can_sync_qty_from_line_weights():
                continue
            net = move._customer_vetting_net_weight_quantity()
            rounded = float_round(
                net,
                precision_rounding=move.product_uom.rounding,
            )
            move.write({'product_uom_qty': rounded})
            for ml in move.move_line_ids.filtered(
                lambda line: line.state not in ('done', 'cancel')
            ):
                qty_ml = move.product_uom._compute_quantity(
                    rounded,
                    ml.product_uom_id,
                    rounding_method='HALF-UP',
                )
                ml.write({'quantity': qty_ml})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        keys = (
            'customer_vetting_gross_weight',
            'customer_vetting_tare_weight',
            'customer_vetting_line_net_weight',
        )
        sync_moves = self.env['stock.move']
        for move, vals in zip(records, vals_list):
            if any(k in vals for k in keys):
                sync_moves |= move
        sync_moves._customer_vetting_sync_product_uom_qty_from_line_weights()
        return records

    def write(self, vals):
        res = super().write(vals)
        keys = (
            'customer_vetting_gross_weight',
            'customer_vetting_tare_weight',
            'customer_vetting_line_net_weight',
        )
        if any(k in vals for k in keys):
            self._customer_vetting_sync_product_uom_qty_from_line_weights()
        return res

    def _inverse_customer_vetting_line_net_weight(self):
        """Keep tare consistent with net (gross − tare = net), resync demand when allowed."""
        for move in self:
            picking = move.picking_id
            if (
                not picking
                or picking.picking_type_id.code != 'incoming'
                or move.state == 'cancel'
            ):
                continue
            gross = move.customer_vetting_gross_weight or 0.0
            net = move.customer_vetting_line_net_weight or 0.0
            net = max(0.0, min(net, gross))
            tare = gross - net
            move.write({'customer_vetting_tare_weight': tare})

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
        'picking_id.picking_type_id',
        'picking_id.picking_type_id.code',
        'customer_vetting_gross_weight',
        'customer_vetting_tare_weight',
    )
    def _compute_customer_vetting_line_weight_display(self):
        for move in self:
            picking = move.picking_id
            if not picking or picking.picking_type_id.code != 'incoming':
                move.customer_vetting_line_total_weight = 0.0
                move.customer_vetting_line_net_weight = 0.0
                move.customer_vetting_line_p_net_weight = 0.0
                continue
            gross = move.customer_vetting_gross_weight or 0.0
            tare = move.customer_vetting_tare_weight or 0.0
            net = gross - tare
            if net < 0:
                net = 0.0
            move.customer_vetting_line_total_weight = gross
            move.customer_vetting_line_net_weight = net
            prec = self.env['decimal.precision'].precision_get('Stock Weight')
            move.customer_vetting_line_p_net_weight = float_round(
                net, precision_digits=prec
            )

    def _get_in_move_lines(self):
        self.ensure_one()
        if (
            self.picking_id
            and self.picking_id._customer_vetting_is_product_detail_so_receipt()
        ):
            return self.env['stock.move.line']
        return super()._get_in_move_lines()
