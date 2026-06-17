# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    service_request_id = fields.Many2one(
        'service.request',
        string='Service request',
        ondelete='set null',
        copy=False,
        index=True,
    )
    required_filtering_quality = fields.Float(
        string='Required filtering quality',
        tracking=True,
        digits=(16, 4),
        help='Mirrors service request value.',
    )
    vetting_detail_line_ids = fields.One2many(
        comodel_name='sale.order.service.detail.line',
        inverse_name='order_id',
        string='Product vetting details',
        copy=False,
    )
    product_detail_receipt_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='customer_vetting_sale_id',
        string='Product detail receipts',
        domain=[('picking_type_id.code', '=', 'incoming')],
        copy=False,
    )
    product_detail_receipt_count = fields.Integer(
        compute='_compute_product_detail_receipt_count',
        string='Product detail receipts',
    )
    customer_vetting_delivery_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='customer_vetting_sale_id',
        string='Customer vetting deliveries',
        domain=[('picking_type_id.code', '=', 'outgoing')],
        copy=False,
    )
    customer_vetting_delivery_count = fields.Integer(
        compute='_compute_customer_vetting_delivery_count',
        string='Deliveries',
    )
    customer_vetting_can_create_delivery = fields.Boolean(
        compute='_compute_customer_vetting_can_create_delivery',
        string='Can create vetting delivery',
    )
    overall_customer_report_ids = fields.One2many(
        'overall.customer.report',
        'sale_order_id',
        string='Overall customer report',
    )

    @api.depends('product_detail_receipt_ids', 'name', 'company_id')
    def _compute_product_detail_receipt_count(self):
        Picking = self.env['stock.picking']
        for order in self:
            pickings = order.product_detail_receipt_ids
            if not pickings and order.name and order.name != '/':
                origin = order._customer_vetting_product_detail_receipt_origin()
                pickings = Picking.search(
                    [
                        ('origin', '=', origin),
                        ('company_id', '=', order.company_id.id),
                        ('picking_type_id.code', '=', 'incoming'),
                    ]
                )
            order.product_detail_receipt_count = len(pickings)

    @api.depends('customer_vetting_delivery_ids')
    def _compute_customer_vetting_delivery_count(self):
        for order in self:
            order.customer_vetting_delivery_count = len(
                order.customer_vetting_delivery_ids.filtered(
                    lambda p: p.state != 'cancel'
                )
            )

    @api.depends(
        'service_request_id',
        'state',
        'product_detail_receipt_ids.customer_vetting_mrp_production_ids.state',
        'product_detail_receipt_ids.customer_vetting_mrp_production_ids.qty_produced',
        'product_detail_receipt_ids.customer_vetting_mrp_production_ids.move_byproduct_ids.quantity',
        'product_detail_receipt_ids.customer_vetting_mrp_production_ids.move_byproduct_ids.state',
        'customer_vetting_delivery_ids.state',
        'customer_vetting_delivery_ids.move_ids_without_package.product_uom_qty',
        'customer_vetting_delivery_ids.move_ids_without_package.quantity',
        'customer_vetting_delivery_ids.move_ids_without_package.state',
    )
    def _compute_customer_vetting_can_create_delivery(self):
        for order in self:
            order.customer_vetting_can_create_delivery = bool(
                order.service_request_id
                and order.state in ('sale', 'done')
                and order._customer_vetting_done_delivery_products()
            )

    def _primary_template_variant(self, template):
        """Return one product.product for a template (or empty recordset)."""
        if not template:
            return self.env['product.product']
        if template.product_variant_id:
            return template.product_variant_id
        return template.product_variant_ids[:1]

    def _customer_vetting_receipt_excluded_finished_variants(self):
        """Product variants that are the configured *finished* output of a service on this order.

        They must not appear on the product-detail incoming receipt (raw / bag only).
        """
        self.ensure_one()
        variants = self.env['product.product']
        for sol in self.order_line.filtered(
            lambda l: not l.display_type and l.product_id and l.product_id.type == 'service'
        ):
            ftmpl = sol.product_id.product_tmpl_id.vetting_finished_product_id
            if ftmpl:
                variants |= self._primary_template_variant(ftmpl)
        return variants

    def _sync_service_vetting_detail_lines(self):
        Detail = self.env['sale.order.service.detail.line']
        for order in self:
            if not order.service_request_id:
                order.vetting_detail_line_ids.unlink()
                continue

            service_lines = order.order_line.filtered(
                lambda l: not l.display_type and l.product_id and l.product_id.type == 'service'
            )
            desired = set()
            sequence = 0

            for sol in service_lines:
                tmpl = sol.product_id.product_tmpl_id

                for dtype, sub_tmpl in (
                    ('other', tmpl.vetting_other_product_id),
                    ('bag', tmpl.bag_id),
                ):
                    if not sub_tmpl:
                        continue
                    variant = order._primary_template_variant(sub_tmpl)
                    if not variant:
                        continue

                    desired.add((sol.id, dtype))
                    sequence += 10
                    desc = variant.get_product_multiline_description_sale() or variant.display_name
                    existing = Detail.search(
                        [
                            ('order_id', '=', order.id),
                            ('source_sale_line_id', '=', sol.id),
                            ('detail_type', '=', dtype),
                        ],
                        limit=1,
                    )

                    if dtype == 'other':
                        vals = {
                            'sequence': sequence,
                            'product_id': variant.id,
                            'product_uom': variant.uom_id.id,
                            'product_uom_qty': sol.product_uom_qty,
                        }
                        if not existing or existing.product_id != variant:
                            vals['name'] = desc
                    else:
                        if existing:
                            vals = {'sequence': sequence}
                            if existing.product_id != variant:
                                vals['product_id'] = variant.id
                                vals['name'] = desc
                                vals['product_uom'] = variant.uom_id.id
                        else:
                            vals = {
                                'sequence': sequence,
                                'product_id': variant.id,
                                'name': desc,
                                'product_uom': variant.uom_id.id,
                                'product_uom_qty': 1.0,
                            }

                    if existing:
                        existing.with_context(customer_vetting_skip_propagate_detail=True).write(
                            vals
                        )
                    else:
                        Detail.create(
                            {
                                **vals,
                                'order_id': order.id,
                                'source_sale_line_id': sol.id,
                                'detail_type': dtype,
                            }
                        )

            orphans = order.vetting_detail_line_ids.filtered(
                lambda d: (d.source_sale_line_id.id, d.detail_type) not in desired
            )
            orphans.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for vals in vals_list:
            v = dict(vals)
            if v.get('service_request_id'):
                req = self.env['service.request'].browse(v['service_request_id'])
                if 'required_filtering_quality' not in v:
                    v['required_filtering_quality'] = req.required_filtering_quality
            prepared.append(v)
        orders = super().create(prepared)
        orders._sync_service_vetting_detail_lines()
        orders._sync_overall_customer_report_lines()
        return orders

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('order_line', 'service_request_id')):
            self._sync_service_vetting_detail_lines()
        if any(k in vals for k in ('order_line', 'service_request_id', 'state')):
            self._sync_overall_customer_report_lines()
        return res

    def _action_confirm(self):
        res = super()._action_confirm()
        self._customer_vetting_create_product_detail_receipts()
        self._sync_overall_customer_report_lines()
        return res

    def _action_cancel(self):
        res = super()._action_cancel()
        self._customer_vetting_cancel_product_detail_receipts()
        return res

    def _customer_vetting_product_detail_receipt_origin(self):
        self.ensure_one()
        return '%s | Product detail' % (self.name,)

    def _customer_vetting_storable_vetting_detail_lines(self):
        self.ensure_one()
        excluded_finished = self._customer_vetting_receipt_excluded_finished_variants()
        return self.vetting_detail_line_ids.filtered(
            lambda l: l.detail_type in ('other', 'bag')
            and l.product_id
            and l.product_id not in excluded_finished
            and l.product_id.is_storable
            and l.product_uom
            and l.product_uom_qty > 0
        )

    def _customer_vetting_create_product_detail_receipts(self):
        Picking = self.env['stock.picking']
        for order in self:
            if not order.service_request_id or not order.vetting_detail_line_ids:
                continue
            storable_lines = order._customer_vetting_storable_vetting_detail_lines()
            if not storable_lines:
                continue
            origin = order._customer_vetting_product_detail_receipt_origin()
            if order.product_detail_receipt_ids.filtered(lambda p: p.state != 'cancel'):
                continue
            if Picking.search(
                [
                    ('origin', '=', origin),
                    ('company_id', '=', order.company_id.id),
                    ('state', '!=', 'cancel'),
                ],
                limit=1,
            ):
                continue
            warehouse = order.warehouse_id or self.env['stock.warehouse'].search(
                [('company_id', '=', order.company_id.id)], limit=1
            )
            if not warehouse:
                raise UserError(
                    _('Configure a warehouse for company %s to create product detail receipts.')
                    % order.company_id.display_name
                )
            picking_type = warehouse.in_type_id
            if not picking_type or not picking_type.default_location_src_id or not picking_type.default_location_dest_id:
                raise UserError(
                    _('Warehouse %s is missing a proper incoming operation type or locations.')
                    % warehouse.display_name
                )
            move_vals = []
            for line in storable_lines:
                move_vals.append(
                    (
                        0,
                        0,
                        {
                            'name': line.name or line.product_id.display_name,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'product_uom_qty': line.product_uom_qty,
                            'location_id': picking_type.default_location_src_id.id,
                            'location_dest_id': picking_type.default_location_dest_id.id,
                            'company_id': order.company_id.id,
                        },
                    )
                )
            picking = Picking.create(
                {
                    'partner_id': order.partner_id.id,
                    'picking_type_id': picking_type.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                    'origin': origin,
                    'company_id': order.company_id.id,
                    'customer_vetting_sale_id': order.id,
                    'move_ids_without_package': move_vals,
                }
            )
            picking.action_confirm()

    def _customer_vetting_cancel_product_detail_receipts(self):
        Picking = self.env['stock.picking']
        for order in self:
            origin = order._customer_vetting_product_detail_receipt_origin()
            receipts = order.product_detail_receipt_ids.filtered(
                lambda p: p.state not in ('done', 'cancel')
            )
            if not receipts:
                receipts = Picking.search(
                    [
                        ('origin', '=', origin),
                        ('company_id', '=', order.company_id.id),
                        ('state', 'not in', ('done', 'cancel')),
                    ]
                )
            receipts.action_cancel()

    def action_view_product_detail_receipts(self):
        self.ensure_one()
        pickings = self.product_detail_receipt_ids
        if not pickings and self.name and self.name != '/':
            origin = self._customer_vetting_product_detail_receipt_origin()
            pickings = self.env['stock.picking'].search(
                [
                    ('origin', '=', origin),
                    ('company_id', '=', self.company_id.id),
                    ('picking_type_id.code', '=', 'incoming'),
                ]
            )
        if not pickings:
            return False
        action = self.env['ir.actions.actions']._for_xml_id('stock.action_picking_tree_incoming')
        action = dict(action)
        if len(pickings) == 1:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if action.get('views'):
                action['views'] = form_view + [
                    (state, view) for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
            action['view_mode'] = 'form'
        else:
            action['domain'] = [('id', 'in', pickings.ids)]
        ref_pick = pickings.filtered(lambda p: p.picking_type_id.code == 'incoming')[:1] or pickings[:1]
        action['context'] = dict(
            self.env.context,
            default_partner_id=self.partner_id.id,
            default_picking_type_id=ref_pick.picking_type_id.id,
            default_origin=self.name,
        )
        return action

    def action_view_customer_vetting_deliveries(self):
        self.ensure_one()
        pickings = self.customer_vetting_delivery_ids.filtered(
            lambda p: p.state != 'cancel'
        )
        if not pickings:
            return False
        action = self.env['ir.actions.actions']._for_xml_id('stock.action_picking_tree_all')
        action = dict(action)
        if len(pickings) == 1:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if action.get('views'):
                action['views'] = form_view + [
                    (state, view) for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
            action['view_mode'] = 'form'
        else:
            action['domain'] = [('id', 'in', pickings.ids)]
        action['context'] = dict(
            self.env.context,
            default_partner_id=self.partner_id.id,
            default_origin=self.name,
            create=False,
        )
        return action

    def _customer_vetting_receipt_mrp_productions(self):
        self.ensure_one()
        receipts = self.product_detail_receipt_ids.filtered(lambda p: p.state != 'cancel')
        if not receipts:
            return self.env['mrp.production']
        return self.env['mrp.production'].search(
            [
                ('customer_vetting_receipt_picking_id', 'in', receipts.ids),
                ('state', '!=', 'cancel'),
            ],
            order='id',
        )

    def _customer_vetting_done_receipt_mrp_productions(self):
        return self._customer_vetting_receipt_mrp_productions().filtered(
            lambda mo: mo.state in ('done', 'to_close')
        )

    def _customer_vetting_delivered_product_qty(self, product, uom):
        """Quantity already on non-cancelled vetting deliveries for this sales order."""
        self.ensure_one()
        total = 0.0
        for picking in self.customer_vetting_delivery_ids.filtered(
            lambda p: p.state != 'cancel'
        ):
            for move in picking.move_ids_without_package.filtered(
                lambda m: m.state != 'cancel' and m.product_id == product
            ):
                qty = move.quantity if move.state == 'done' else move.product_uom_qty
                total += move.product_uom._compute_quantity(
                    qty, uom, rounding_method='HALF-UP'
                )
        return total

    def _customer_vetting_done_delivery_products(self):
        """Aggregate produced qty per product from done MOs minus already delivered."""
        self.ensure_one()
        aggregates = {}
        for mo in self._customer_vetting_done_receipt_mrp_productions():
            for product, src_uom, qty, line_type in mo._customer_vetting_done_production_lines():
                if not product.is_storable or qty <= 0:
                    continue
                key = product.id
                if key not in aggregates:
                    aggregates[key] = {
                        'product': product,
                        'uom': src_uom,
                        'produced_qty': 0.0,
                        'line_type': line_type,
                        'mo_ids': set(),
                    }
                entry = aggregates[key]
                entry['produced_qty'] += src_uom._compute_quantity(
                    qty, entry['uom'], rounding_method='HALF-UP'
                )
                entry['mo_ids'].add(mo.id)
        result = []
        for entry in aggregates.values():
            product = entry['product']
            uom = entry['uom']
            delivered = self._customer_vetting_delivered_product_qty(product, uom)
            available = float_round(
                entry['produced_qty'] - delivered,
                precision_rounding=uom.rounding,
            )
            if available > 0:
                result.append({
                    'product': product,
                    'uom': uom,
                    'available_qty': available,
                    'line_type': entry['line_type'],
                    'mo_ids': list(entry['mo_ids']),
                })
        return result

    def _customer_vetting_prepare_delivery_wizard_lines(self):
        self.ensure_one()
        lines = []
        for item in self._customer_vetting_done_delivery_products():
            lines.append(
                (
                    0,
                    0,
                    {
                        'mrp_production_ids': [(6, 0, item['mo_ids'])],
                        'line_type': item['line_type'],
                        'product_id': item['product'].id,
                        'product_uom_id': item['uom'].id,
                        'available_qty': item['available_qty'],
                        'product_uom_qty': item['available_qty'],
                        'selected': True,
                    },
                )
            )
        return lines

    def action_open_create_delivery_wizard(self):
        self.ensure_one()
        if self.state not in ('sale', 'done'):
            raise UserError(
                _('Delivery orders can only be created on confirmed sales orders.')
            )
        if not self.service_request_id:
            raise UserError(_('This sales order is not linked to a service request.'))
        if not self._customer_vetting_done_receipt_mrp_productions():
            raise UserError(
                _('No done manufacturing orders were found from product detail receipts.')
            )
        wizard_lines = self._customer_vetting_prepare_delivery_wizard_lines()
        if not wizard_lines:
            raise UserError(
                _('No finished products or by-products are available to deliver.')
            )
        wizard = self.env['customer.vetting.create.delivery.wizard'].create(
            {
                'sale_order_id': self.id,
                'line_ids': wizard_lines,
            }
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create delivery order'),
            'res_model': 'customer.vetting.create.delivery.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _customer_vetting_create_delivery_picking(self, line_specs):
        """Create one outgoing delivery from wizard line specs.

        line_specs: list of dicts with keys product_id, product_uom_id,
        product_uom_qty, mrp_production_ids.
        """
        self.ensure_one()
        Picking = self.env['stock.picking']
        StockMove = self.env['stock.move']
        if not line_specs:
            return Picking
        warehouse = self.warehouse_id or self.env['stock.warehouse'].search(
            [('company_id', '=', self.company_id.id)], limit=1
        )
        if not warehouse:
            raise UserError(
                _('Configure a warehouse for company %s to create delivery orders.')
                % self.company_id.display_name
            )
        picking_type = warehouse.out_type_id
        if (
            not picking_type
            or not picking_type.default_location_src_id
            or not picking_type.default_location_dest_id
        ):
            raise UserError(
                _('Warehouse %s is missing a proper outgoing operation type or locations.')
                % warehouse.display_name
            )
        move_vals = []
        all_mo_ids = set()
        for spec in line_specs:
            product = spec['product_id']
            uom = spec['product_uom_id']
            qty = spec['product_uom_qty']
            mo_records = spec.get('mrp_production_ids') or self.env['mrp.production']
            mo = mo_records[:1]
            all_mo_ids.update(mo_records.ids)
            sol = mo._customer_vetting_service_sale_line() if mo else self.env['sale.order.line']
            if not sol:
                for order_line in self.order_line.filtered(
                    lambda l: not l.display_type and l.product_id
                ):
                    if order_line.product_id == product:
                        sol = order_line
                        break
            vals = {
                'name': product.display_name,
                'product_id': product.id,
                'product_uom': uom.id,
                'product_uom_qty': qty,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'company_id': self.company_id.id,
            }
            if sol and 'sale_line_id' in StockMove._fields:
                vals['sale_line_id'] = sol.id
            if mo and 'customer_vetting_mrp_production_id' in StockMove._fields:
                vals['customer_vetting_mrp_production_id'] = mo.id
            move_vals.append((0, 0, vals))
        all_mo_ids = list(all_mo_ids)
        picking_vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'origin': '%s | Delivery' % self.name,
            'company_id': self.company_id.id,
            'customer_vetting_sale_id': self.id,
            'customer_vetting_mrp_production_id': all_mo_ids[0] if len(all_mo_ids) == 1 else False,
            'move_ids_without_package': move_vals,
        }
        if self.procurement_group_id:
            picking_vals['group_id'] = self.procurement_group_id.id
        picking = Picking.with_context(customer_vetting_skip_valuation=True).create(
            picking_vals
        )
        picking.action_confirm()
        picking._customer_vetting_sync_delivery_move_quantity_to_demand()
        for mo_id in all_mo_ids:
            mo = self.env['mrp.production'].browse(mo_id)
            mo.message_post(
                body=_(
                    'Delivery order %(name)s created for finished product and by-products.',
                    name=picking.display_name,
                )
            )
        return picking

    def _sync_overall_customer_report_lines(self):
        """Create or update one overall customer report row per service sales order."""
        Report = self.env['overall.customer.report'].sudo()
        for order in self:
            if not order.service_request_id or order.state not in ('sale', 'done'):
                Report.search([('sale_order_id', '=', order.id)]).unlink()
                continue
            main_line = order.order_line.filtered(
                lambda l: not l.display_type and l.product_id
            )[:1]
            if not main_line:
                Report.search([('sale_order_id', '=', order.id)]).unlink()
                continue
            rec = Report.search([('sale_order_id', '=', order.id)], limit=1)
            if not rec:
                rec = Report.create({
                    'sale_order_id': order.id,
                    'sale_line_id': main_line.id,
                })
            elif rec.sale_line_id != main_line:
                rec.sale_line_id = main_line.id
            rec._recompute_quantities()

    _sql_constraints = [
        (
            'customer_vetting_service_request_unique',
            'unique(service_request_id)',
            'Each service request can only be linked to one sales order.',
        ),
    ]
