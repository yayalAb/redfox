# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_round


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    customer_vetting_product_detail_receipt = fields.Boolean(
        string='Product detail vetting receipt',
        compute='_compute_customer_vetting_product_detail_receipt',
        store=True,
        help='Technical: used to keep weighbridge line fields editable after validation.',
    )
    customer_vetting_sale_id = fields.Many2one(
        'sale.order',
        string='Sales order (customer vetting)',
        ondelete='set null',
        copy=False,
        index=True,
    )
    customer_vetting_mrp_production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing order (customer vetting delivery)',
        ondelete='set null',
        copy=False,
        index=True,
    )
    customer_vetting_cdn_required_filtering_quality = fields.Float(
        string='Required filtering quality (CDN)',
        compute='_compute_customer_vetting_cdn_required_filtering_quality',
        digits=(16, 4),
        help='Sale order required filtering quality for delivery note printout.',
    )
    customer_vetting_mrp_production_ids = fields.One2many(
        'mrp.production',
        'customer_vetting_receipt_picking_id',
        string='Manufacturing orders',
    )
    customer_vetting_mrp_production_count = fields.Integer(
        compute='_compute_customer_vetting_mrp_production_count',
        string='Manufacturing orders',
    )

    @api.depends('customer_vetting_mrp_production_ids')
    def _compute_customer_vetting_mrp_production_count(self):
        for picking in self:
            picking.customer_vetting_mrp_production_count = len(
                picking.customer_vetting_mrp_production_ids
            )

    @api.depends(
        'customer_vetting_sale_id',
        'customer_vetting_sale_id.required_filtering_quality',
        'origin',
        'company_id',
    )
    def _compute_customer_vetting_cdn_required_filtering_quality(self):
        for picking in self:
            order = picking.customer_vetting_sale_id
            if not order:
                order = picking._customer_vetting_product_detail_receipt_sale_order()
            picking.customer_vetting_cdn_required_filtering_quality = (
                (order.required_filtering_quality or 0.0) if order else 0.0
            )

    @api.depends('customer_vetting_sale_id', 'origin')
    def _compute_customer_vetting_product_detail_receipt(self):
        for picking in self:
            picking.customer_vetting_product_detail_receipt = (
                picking._customer_vetting_is_product_detail_so_receipt()
            )

    def _customer_vetting_is_product_detail_so_receipt(self):
        """True for incoming transfers created from the sales order product-detail vetting flow."""
        self.ensure_one()
        if self.customer_vetting_sale_id:
            return True
        origin = (self.origin or '').strip()
        return bool(origin.endswith(' | Product detail'))

    def _customer_vetting_linked_sale_order(self):
        """Resolve the vetting sales order from FK, backorder chain, or origin."""
        self.ensure_one()
        if self.customer_vetting_sale_id:
            return self.customer_vetting_sale_id
        picking = self
        while picking.backorder_id:
            if picking.backorder_id.customer_vetting_sale_id:
                return picking.backorder_id.customer_vetting_sale_id
            picking = picking.backorder_id
        if self._customer_vetting_is_product_detail_so_receipt():
            return self._customer_vetting_product_detail_receipt_sale_order_from_origin()
        if self._customer_vetting_is_delivery_so_picking():
            return self._customer_vetting_delivery_sale_order_from_origin()
        return self.env['sale.order']

    def _customer_vetting_is_delivery_so_picking(self):
        """True for outgoing vetting deliveries linked to a sales order."""
        self.ensure_one()
        if self.picking_type_id.code != 'outgoing':
            return False
        if self.customer_vetting_sale_id:
            return True
        origin = (self.origin or '').strip()
        return origin.endswith(' | Delivery')

    def _customer_vetting_product_detail_receipt_sale_order_from_origin(self):
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

    def _customer_vetting_delivery_sale_order_from_origin(self):
        origin = (self.origin or '').strip()
        marker = ' | Delivery'
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

    def _customer_vetting_product_detail_receipt_sale_order(self):
        """Resolve the sales order for a product-detail receipt (FK or legacy origin)."""
        self.ensure_one()
        order = self._customer_vetting_linked_sale_order()
        if order:
            return order
        return self._customer_vetting_product_detail_receipt_sale_order_from_origin()

    def _customer_vetting_sync_delivery_move_quantity_to_demand(self):
        """Set move quantity to demand on vetting delivery orders."""
        for picking in self:
            if (
                picking.picking_type_id.code != 'outgoing'
                or not picking._customer_vetting_is_delivery_so_picking()
            ):
                continue
            for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                if float_is_zero(
                    move.product_uom_qty, precision_rounding=move.product_uom.rounding
                ):
                    continue
                if float_is_zero(move.quantity, precision_rounding=move.product_uom.rounding):
                    move.quantity = move.product_uom_qty

    def _create_backorder_picking(self):
        self.ensure_one()
        copy_vals = {
            'name': '/',
            'move_ids': [],
            'move_line_ids': [],
            'backorder_id': self.id,
        }
        sale_order = self._customer_vetting_linked_sale_order()
        if sale_order and self.picking_type_id.code == 'incoming':
            if self._customer_vetting_is_product_detail_so_receipt():
                copy_vals['customer_vetting_sale_id'] = sale_order.id
                copy_vals['origin'] = sale_order._customer_vetting_product_detail_receipt_origin()
        elif sale_order and self.picking_type_id.code == 'outgoing':
            if self._customer_vetting_is_delivery_so_picking():
                copy_vals['customer_vetting_sale_id'] = sale_order.id
                copy_vals['origin'] = self.origin or '%s | Delivery' % sale_order.name
                if self.customer_vetting_mrp_production_id:
                    copy_vals['customer_vetting_mrp_production_id'] = (
                        self.customer_vetting_mrp_production_id.id
                    )
        return self.copy(copy_vals)

    def _customer_vetting_good_receiving_report_moves(self):
        """Moves to print on Customer Good Receiving Note.

        Product-detail vetting receipts: only raw + bag lines (not finished output).
        Other receipts: all non-cancelled operations lines.
        """
        self.ensure_one()
        moves = self.move_ids_without_package.filtered(lambda m: m.state != 'cancel')
        if not self._customer_vetting_is_product_detail_so_receipt():
            return moves
        order = self._customer_vetting_product_detail_receipt_sale_order()
        if not order:
            return moves
        excluded = order._customer_vetting_receipt_excluded_finished_variants()
        detail_products = order.vetting_detail_line_ids.filtered(
            lambda l: l.detail_type in ('other', 'bag') and l.product_id
        ).mapped('product_id')
        if detail_products:
            return moves.filtered(lambda m: m.product_id in detail_products)
        return moves.filtered(lambda m: m.product_id not in excluded)

    def _grn_good_receiving_report_moves(self):
        """Delegate to vetting filtering when this module is installed."""
        return self._customer_vetting_good_receiving_report_moves()

    def _customer_vetting_is_reception_report_action(self, action):
        return isinstance(action, dict) and action.get('tag') == 'reception_report'

    def _customer_vetting_without_reception_report_redirect(self, result):
        """Do not open the allocation / reception report after validating vetting receipts."""
        if self._customer_vetting_is_reception_report_action(result):
            return True
        if isinstance(result, dict) and result.get('tag') == 'do_multi_print':
            params = dict(result.get('params') or {})
            another = params.pop('anotherAction', None)
            if self._customer_vetting_is_reception_report_action(another):
                if params.get('reports'):
                    return {**result, 'params': params}
                return True
        return result

    def button_validate(self):
        res = super().button_validate()
        if self.filtered(lambda p: p._customer_vetting_is_product_detail_so_receipt()):
            return self._customer_vetting_without_reception_report_redirect(res)
        return res

    def _action_done(self):
        res = super()._action_done()
        self._customer_vetting_create_mrp_from_done_receipt()
        self._customer_vetting_refresh_overall_customer_reports()
        return res

    def _customer_vetting_refresh_overall_customer_reports(self):
        orders = self.env['sale.order']
        for picking in self:
            order = picking._customer_vetting_linked_sale_order()
            if order and order.service_request_id:
                orders |= order
        if not orders:
            return
        reports = self.env['overall.customer.report'].sudo().search(
            [('sale_order_id', 'in', orders.ids)]
        )
        if reports:
            reports._recompute_quantities()

    def action_view_customer_vetting_mrp_productions(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('mrp.mrp_production_action')
        action = dict(action)
        productions = self.customer_vetting_mrp_production_ids
        if len(productions) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = productions.id
            action['views'] = [(False, 'form')]
        else:
            action['domain'] = [('id', 'in', productions.ids)]
        action['context'] = dict(self.env.context, create=False)
        return action

    def _customer_vetting_mrp_picking_type(self, bom, order):
        """Manufacturing operation type required to create MOs (sequence + locations)."""
        PickingType = self.env['stock.picking.type']
        company = order.company_id
        candidates = []
        if bom.picking_type_id and bom.picking_type_id.company_id == company:
            candidates.append(bom.picking_type_id)
        warehouse = order.warehouse_id or self.env['stock.warehouse'].search(
            [('company_id', '=', company.id)], limit=1
        )
        if warehouse and warehouse.manu_type_id:
            candidates.append(warehouse.manu_type_id)
        default_id = self.env['mrp.production']._get_default_picking_type_id(company.id)
        if default_id:
            candidates.append(PickingType.browse(default_id))
        for picking_type in candidates:
            if picking_type and picking_type.sequence_id:
                return picking_type
        raise UserError(
            _(
                'Cannot create a manufacturing order for company %(company)s: '
                'no manufacturing operation type with a sequence is configured. '
                'Check Inventory → Configuration → Warehouses (manufacturing steps) '
                'or set an operation type on the bill of materials.',
                company=company.display_name,
            )
        )

    def _customer_vetting_mo_qty_for_service_receipt(
        self, sale_line, raw_detail, finished_product
    ):
        """Quantity to manufacture: prefer done raw qty on this receipt (converted), else service line qty."""
        self.ensure_one()
        if raw_detail and raw_detail.product_id:
            moves = self.move_ids.filtered(
                lambda m: m.product_id == raw_detail.product_id and m.state == 'done'
            )
            if moves:
                total = 0.0
                for move in moves:
                    if move.quantity <= 0:
                        continue
                    total += move.product_uom._compute_quantity(
                        move.quantity,
                        finished_product.uom_id,
                        rounding_method='HALF-UP',
                    )
                if total > 0:
                    return float_round(
                        total,
                        precision_rounding=finished_product.uom_id.rounding,
                    )
        qty = sale_line.product_uom_qty
        if sale_line.product_uom and sale_line.product_uom.category_id == finished_product.uom_id.category_id:
            qty = sale_line.product_uom._compute_quantity(
                qty,
                finished_product.uom_id,
                rounding_method='HALF-UP',
            )
        return float_round(qty, precision_rounding=finished_product.uom_id.rounding)

    def _customer_vetting_create_mrp_from_done_receipt(self):
        """After validating a product-detail incoming receipt, draft MOs for finished goods (service template)."""
        MrpProduction = self.env['mrp.production']
        Bom = self.env['mrp.bom']
        if self.env.context.get('customer_vetting_skip_mrp_from_receipt'):
            return
        for picking in self:
            if picking.picking_type_id.code != 'incoming':
                continue
            if not picking._customer_vetting_is_product_detail_so_receipt():
                continue
            order = picking._customer_vetting_product_detail_receipt_sale_order()
            if not order or not order.service_request_id:
                continue
            for sol in order.order_line.filtered(
                lambda l: not l.display_type and l.product_id and l.product_id.type == 'service'
            ):
                ftmpl = sol.product_id.product_tmpl_id.vetting_finished_product_id
                if not ftmpl:
                    continue
                finished = order._primary_template_variant(ftmpl)
                if not finished:
                    continue
                dup_domain = [
                    ('customer_vetting_receipt_picking_id', '=', picking.id),
                    ('product_id', '=', finished.id),
                    ('state', '!=', 'cancel'),
                ]
                if 'sale_line_id' in MrpProduction._fields:
                    dup_domain.append(('sale_line_id', '=', sol.id))
                if MrpProduction.search(dup_domain, limit=1):
                    continue
                bom_map = Bom.with_context(active_test=True)._bom_find(
                    finished,
                    company_id=order.company_id.id,
                    bom_type='normal',
                )
                bom = bom_map[finished]
                if not bom:
                    picking.message_post(
                        body=_(
                            'No bill of materials found for %(product)s. '
                            'No manufacturing order was created from this receipt.',
                            product=finished.display_name,
                        )
                    )
                    continue
                raw_detail = order.vetting_detail_line_ids.filtered(
                    lambda l: l.source_sale_line_id == sol and l.detail_type == 'other'
                )[:1]
                mo_qty = picking._customer_vetting_mo_qty_for_service_receipt(
                    sol, raw_detail, finished
                )
                if mo_qty <= 0:
                    continue
                picking_type = picking._customer_vetting_mrp_picking_type(bom, order)
                vals = {
                    'bom_id': bom.id,
                    'product_id': finished.id,
                    'product_qty': mo_qty,
                    'product_uom_id': finished.uom_id.id,
                    'picking_type_id': picking_type.id,
                    'origin': '%s | %s' % (order.name, picking.name),
                    'company_id': order.company_id.id,
                    'customer_vetting_receipt_picking_id': picking.id,
                }
                if 'sale_line_id' in MrpProduction._fields:
                    vals['sale_line_id'] = sol.id
                mo = MrpProduction.create(vals)
                mo.action_confirm()
                picking.message_post(
                    body=_(
                        'Manufacturing order %(name)s created for %(product)s.',
                        name=mo.display_name,
                        product=finished.display_name,
                    )
                )
