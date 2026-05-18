# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import float_round


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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
    customer_vetting_plate_no = fields.Char(
        string='Plate No.',
        copy=False,
    )
    customer_vetting_sale_id = fields.Many2one(
        'sale.order',
        string='Sales order (product detail receipt)',
        ondelete='set null',
        copy=False,
        index=True,
    )

    def _customer_vetting_is_product_detail_so_receipt(self):
        """True for incoming transfers created from the sales order product-detail vetting flow."""
        self.ensure_one()
        if self.customer_vetting_sale_id:
            return True
        origin = (self.origin or '').strip()
        return bool(origin.endswith(' | Product detail'))

    def _customer_vetting_product_detail_receipt_sale_order(self):
        """Resolve the sales order for a product-detail receipt (FK or legacy origin)."""
        self.ensure_one()
        if self.customer_vetting_sale_id:
            return self.customer_vetting_sale_id
        origin = (self.origin or '').strip()
        marker = ' | Product detail'
        if not origin.endswith(marker):
            return self.env['sale.order']
        name = origin[: -len(marker)]
        return self.env['sale.order'].search(
            [
                ('name', '=', name),
                ('company_id', '=', self.company_id.id),
            ],
            limit=1,
        )

    def _customer_vetting_net_weight_quantity(self):
        """Net weight (gross - tare), non-negative, for raw-line sync."""
        self.ensure_one()
        gross = self.customer_vetting_gross_weight or 0.0
        tare = self.customer_vetting_tare_weight or 0.0
        net = gross - tare
        return net if net > 0 else 0.0

    def _customer_vetting_sync_raw_move_qty_from_weights(self):
        """Set demand (and move line qty) for raw-product moves to gross - tare.

        Only call this after DB rows exist (picking write/create). Do not use from
        @api.onchange: stock.move.write posts chatter using real ids and breaks on NewId.
        """
        for picking in self:
            if picking.state in ('done', 'cancel'):
                continue
            if picking.picking_type_id.code != 'incoming':
                continue
            if not picking._customer_vetting_is_product_detail_so_receipt():
                continue
            order = picking._customer_vetting_product_detail_receipt_sale_order()
            if not order:
                continue
            raw_products = order.vetting_detail_line_ids.filtered(
                lambda l: l.detail_type == 'other'
                and l.product_id
                and l.product_id.is_storable
            ).mapped('product_id')
            if not raw_products:
                continue
            net = picking._customer_vetting_net_weight_quantity()
            moves = picking.move_ids.filtered(
                lambda m: m.product_id in raw_products
                and m.state not in ('done', 'cancel')
            )
            for move in moves:
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
        keys = ('customer_vetting_gross_weight', 'customer_vetting_tare_weight')
        for picking, vals in zip(records, vals_list):
            if any(k in vals for k in keys):
                picking._customer_vetting_sync_raw_move_qty_from_weights()
        return records

    def write(self, vals):
        res = super().write(vals)
        keys = ('customer_vetting_gross_weight', 'customer_vetting_tare_weight')
        if any(k in vals for k in keys):
            self._customer_vetting_sync_raw_move_qty_from_weights()
        return res
