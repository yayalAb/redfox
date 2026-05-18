# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    service_request_id = fields.Many2one(
        'service.request',
        string='Service request',
        ondelete='set null',
        copy=False,
        index=True,
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
        copy=False,
    )
    product_detail_receipt_count = fields.Integer(
        compute='_compute_product_detail_receipt_count',
        string='Product detail receipts',
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

    def _primary_template_variant(self, template):
        """Return one product.product for a template (or empty recordset)."""
        if not template:
            return self.env['product.product']
        if template.product_variant_id:
            return template.product_variant_id
        return template.product_variant_ids[:1]

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
                    ('finished', tmpl.vetting_finished_product_id),
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

                    if dtype in ('other', 'finished'):
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
        orders = super().create(vals_list)
        orders._sync_service_vetting_detail_lines()
        return orders

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('order_line', 'service_request_id')):
            self._sync_service_vetting_detail_lines()
        return res

    def _action_confirm(self):
        res = super()._action_confirm()
        self._customer_vetting_create_product_detail_receipts()
        return res

    def _action_cancel(self):
        res = super()._action_cancel()
        self._customer_vetting_cancel_product_detail_receipts()
        return res

    def _customer_vetting_product_detail_receipt_origin(self):
        self.ensure_one()
        return '%s | Product detail' % (self.name,)

    def _customer_vetting_create_product_detail_receipts(self):
        Picking = self.env['stock.picking']
        for order in self:
            if not order.service_request_id or not order.vetting_detail_line_ids:
                continue
            storable_lines = order.vetting_detail_line_ids.filtered(
                lambda l: l.detail_type != 'finished'
                and l.product_id
                and l.product_id.is_storable
                and l.product_uom
                and l.product_uom_qty > 0
            )
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

    _sql_constraints = [
        (
            'customer_vetting_service_request_unique',
            'unique(service_request_id)',
            'Each service request can only be linked to one sales order.',
        ),
    ]
