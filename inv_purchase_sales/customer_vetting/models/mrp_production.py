# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    customer_vetting_receipt_picking_id = fields.Many2one(
        'stock.picking',
        string='Customer vetting receipt',
        ondelete='set null',
        copy=False,
        index=True,
        help='Incoming product-detail receipt validated to create this manufacturing order.',
    )
    customer_vetting_delivery_picking_ids = fields.One2many(
        'stock.picking',
        'customer_vetting_mrp_production_id',
        string='Customer vetting deliveries',
        copy=False,
    )
    customer_vetting_delivery_count = fields.Integer(
        compute='_compute_customer_vetting_delivery_count',
        string='Deliveries',
    )

    @api.depends('customer_vetting_delivery_picking_ids')
    def _compute_customer_vetting_delivery_count(self):
        for production in self:
            production.customer_vetting_delivery_count = len(
                production.customer_vetting_delivery_picking_ids.filtered(
                    lambda p: p.state != 'cancel'
                )
            )

    def _customer_vetting_sale_order(self):
        self.ensure_one()
        if self.sale_line_id:
            return self.sale_line_id.order_id
        receipt = self.customer_vetting_receipt_picking_id
        if receipt:
            return receipt._customer_vetting_product_detail_receipt_sale_order()
        return self.env['sale.order']

    def _customer_vetting_service_sale_line(self):
        """Service line on the linked sale order for this MO."""
        self.ensure_one()
        order = self._customer_vetting_sale_order()
        if not order:
            return self.env['sale.order.line']
        if self.sale_line_id and self.sale_line_id in order.order_line:
            return self.sale_line_id
        for sol in order.order_line.filtered(
            lambda l: not l.display_type and l.product_id and l.product_id.type == 'service'
        ):
            ftmpl = sol.product_id.product_tmpl_id.vetting_finished_product_id
            if not ftmpl:
                continue
            finished = order._primary_template_variant(ftmpl)
            if finished and finished == self.product_id:
                return sol
        return self.env['sale.order.line']

    def _customer_vetting_delivery_move_lines(self):
        """(product, uom, qty) tuples for finished product and by-products."""
        self.ensure_one()
        lines = []
        finished = self.product_id
        if finished and self.product_qty > 0:
            lines.append((finished, self.product_uom_id, self.product_qty))
        for move in self.move_byproduct_ids.filtered(lambda m: m.state != 'cancel'):
            qty = move.product_uom_qty
            if qty > 0:
                lines.append((move.product_id, move.product_uom, qty))
        if not self.move_byproduct_ids:
            sol = self._customer_vetting_service_sale_line()
            residue_tmpl = (
                sol.product_id.product_tmpl_id.vetting_residue_product_id
                if sol and sol.product_id
                else False
            )
            order = self._customer_vetting_sale_order()
            if residue_tmpl and order:
                residue = order._primary_template_variant(residue_tmpl)
                if residue and residue not in [p for p, _u, _q in lines]:
                    lines.append((residue, residue.uom_id, self.product_qty))
        return lines

    def _customer_vetting_create_delivery_orders(self):
        """Draft outgoing delivery for finished product and by-products (customer vetting MO)."""
        Picking = self.env['stock.picking']
        if self.env.context.get('customer_vetting_skip_mo_delivery'):
            return self.env['stock.picking']
        created = self.env['stock.picking']
        for mo in self:
            if not mo.customer_vetting_receipt_picking_id:
                continue
            order = mo._customer_vetting_sale_order()
            if not order or not order.service_request_id:
                continue
            if Picking.search(
                [
                    ('customer_vetting_mrp_production_id', '=', mo.id),
                    ('state', '!=', 'cancel'),
                ],
                limit=1,
            ):
                continue
            move_lines = mo._customer_vetting_delivery_move_lines()
            storable = [
                (product, uom, qty)
                for product, uom, qty in move_lines
                if product.is_storable and qty > 0
            ]
            if not storable:
                continue
            warehouse = order.warehouse_id or self.env['stock.warehouse'].search(
                [('company_id', '=', order.company_id.id)], limit=1
            )
            if not warehouse:
                raise UserError(
                    _('Configure a warehouse for company %s to create delivery orders.')
                    % order.company_id.display_name
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
            sol = mo._customer_vetting_service_sale_line()
            move_vals = []
            for product, uom, qty in storable:
                rounded_qty = float_round(qty, precision_rounding=uom.rounding)
                vals = {
                    'name': product.display_name,
                    'product_id': product.id,
                    'product_uom': uom.id,
                    'product_uom_qty': rounded_qty,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                    'company_id': order.company_id.id,
                }
                if sol and 'sale_line_id' in self.env['stock.move']._fields:
                    vals['sale_line_id'] = sol.id
                move_vals.append((0, 0, vals))
            picking_vals = {
                'partner_id': order.partner_id.id,
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'origin': '%s | %s' % (order.name, mo.name),
                'company_id': order.company_id.id,
                'customer_vetting_sale_id': order.id,
                'customer_vetting_mrp_production_id': mo.id,
                'move_ids_without_package': move_vals,
            }
            if order.procurement_group_id:
                picking_vals['group_id'] = order.procurement_group_id.id
            picking = Picking.with_context(
                customer_vetting_skip_valuation=True,
            ).create(picking_vals)
            picking.action_confirm()
            created |= picking
            mo.message_post(
                body=_(
                    'Delivery order %(name)s created for finished product and by-products.',
                    name=picking.display_name,
                )
            )
        return created

    def action_view_customer_vetting_deliveries(self):
        self.ensure_one()
        pickings = self.customer_vetting_delivery_picking_ids.filtered(
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
        action['context'] = dict(self.env.context, create=False)
        return action
