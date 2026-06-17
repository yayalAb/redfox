# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round


class OverallCustomerReport(models.Model):
    _name = 'overall.customer.report'
    _description = 'Overall customer report'
    _order = 'sale_order_id desc, id'
    _rec_name = 'display_name'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sales order line',
        ondelete='cascade',
        index=True,
        help='Primary sales order line (totals are per sales order).',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='sale_order_id.partner_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related='sale_order_id.company_id',
        store=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='sale_line_id.product_id',
        store=True,
        readonly=True,
    )
    product_name = fields.Char(
        string='Product name',
        compute='_compute_product_name',
        store=True,
    )
    raw_product_id = fields.Many2one(
        'product.product',
        string='Raw material (RM)',
        compute='_compute_vetting_products',
        store=True,
    )
    finished_product_id = fields.Many2one(
        'product.product',
        string='Finished product',
        compute='_compute_vetting_products',
        store=True,
    )
    reject_product_id = fields.Many2one(
        'product.product',
        string='Reject product',
        compute='_compute_vetting_products',
        store=True,
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of measure',
        compute='_compute_vetting_products',
        store=True,
    )
    total_received = fields.Float(
        string='Total received (RM)',
        digits='Product Unit of Measure',
        readonly=True,
    )
    total_delivered = fields.Float(
        string='Total delivered',
        digits='Product Unit of Measure',
        readonly=True,
    )
    total_reject = fields.Float(
        string='Reject',
        digits='Product Unit of Measure',
        readonly=True,
    )
    display_name = fields.Char(compute='_compute_display_name', store=True)

    _sql_constraints = [
        (
            'overall_report_unique_sale_order',
            'unique(sale_order_id)',
            'Each sales order can only have one overall customer report row.',
        ),
    ]

    @api.depends(
        'sale_line_id',
        'sale_line_id.product_id',
        'sale_line_id.name',
        'sale_order_id.order_line.product_id',
        'sale_order_id.order_line.name',
        'sale_order_id.order_line.display_type',
    )
    def _compute_product_name(self):
        for report in self:
            order = report.sale_order_id
            if not order:
                report.product_name = False
                continue
            lines = order.order_line.filtered(
                lambda l: not l.display_type and (l.product_id or l.name)
            )
            names = []
            for line in lines:
                if line.product_id:
                    names.append(line.product_id.display_name)
                elif line.name:
                    names.append(line.name)
            report.product_name = ', '.join(names) if names else False

    @api.depends(
        'sale_line_id',
        'sale_line_id.product_id',
        'sale_order_id.vetting_detail_line_ids.product_id',
        'sale_order_id.vetting_detail_line_ids.detail_type',
        'sale_order_id.vetting_detail_line_ids.source_sale_line_id',
    )
    def _compute_vetting_products(self):
        for report in self:
            raw, finished, reject, uom = report._vetting_products_for_line()
            report.raw_product_id = raw
            report.finished_product_id = finished
            report.reject_product_id = reject
            report.product_uom_id = uom

    @api.depends('sale_order_id', 'product_name', 'partner_id')
    def _compute_display_name(self):
        for report in self:
            parts = [
                report.sale_order_id.name or '',
                report.partner_id.display_name or '',
                report.product_name or '',
            ]
            report.display_name = ' / '.join(p for p in parts if p)

    def _vetting_service_line(self):
        """Service line used to resolve RM / finished / reject products."""
        self.ensure_one()
        order = self.sale_order_id
        sol = self.sale_line_id
        if sol and sol.product_id and sol.product_id.type == 'service':
            return sol
        return order.order_line.filtered(
            lambda l: not l.display_type and l.product_id and l.product_id.type == 'service'
        )[:1]

    def _vetting_products_for_line(self):
        self.ensure_one()
        order = self.sale_order_id
        sol = self._vetting_service_line()
        Product = self.env['product.product']
        if not sol or not sol.product_id:
            return Product, Product, Product, False
        tmpl = sol.product_id.product_tmpl_id
        raw = order._primary_template_variant(tmpl.vetting_other_product_id)
        detail = order.vetting_detail_line_ids.filtered(
            lambda d: d.source_sale_line_id == sol and d.detail_type == 'other'
        )[:1]
        if detail.product_id:
            raw = detail.product_id
        finished = order._primary_template_variant(tmpl.vetting_finished_product_id)
        reject = order._primary_template_variant(tmpl.vetting_residue_product_id)
        uom = (
            (raw and raw.uom_id)
            or (finished and finished.uom_id)
            or (reject and reject.uom_id)
            or sol.product_uom
        )
        return raw, finished, reject, uom

    def _reject_product_ids(self):
        self.ensure_one()
        raw, finished, reject, _uom = self._vetting_products_for_line()
        reject_ids = set()
        if reject:
            reject_ids.add(reject.id)
        finished_ids = {finished.id} if finished else set()
        if raw:
            finished_ids.add(raw.id)
        order = self.sale_order_id
        sol = self._vetting_service_line()
        for mo in order._customer_vetting_receipt_mrp_productions():
            mo_sol = mo._customer_vetting_service_sale_line()
            if mo_sol and sol and mo_sol != sol:
                continue
            for move in mo.move_byproduct_ids.filtered(lambda m: m.state != 'cancel'):
                if move.product_id and move.product_id.id not in finished_ids:
                    reject_ids.add(move.product_id.id)
        return list(reject_ids)

    def _sum_done_picking_qty(self, pickings, products):
        if not products:
            return 0.0
        product_set = set(products.ids if hasattr(products, 'ids') else products)
        if not product_set:
            return 0.0
        total = 0.0
        ref_uom = self.product_uom_id
        for picking in pickings.filtered(lambda p: p.state == 'done'):
            for move in picking.move_ids_without_package.filtered(
                lambda m: m.state == 'done' and m.product_id.id in product_set
            ):
                qty = move.quantity
                if ref_uom:
                    qty = move.product_uom._compute_quantity(
                        qty, ref_uom, rounding_method='HALF-UP'
                    )
                total += qty
        if ref_uom:
            return float_round(total, precision_rounding=ref_uom.rounding)
        return total

    def _recompute_quantities(self):
        for report in self:
            order = report.sale_order_id
            raw, finished, _reject, _uom = report._vetting_products_for_line()
            receipts = order.product_detail_receipt_ids
            deliveries = order.customer_vetting_delivery_ids
            reject_ids = report._reject_product_ids()
            vals = {
                'total_received': report._sum_done_picking_qty(receipts, raw),
                'total_delivered': report._sum_done_picking_qty(deliveries, finished),
                'total_reject': report._sum_done_picking_qty(
                    deliveries,
                    self.env['product.product'].browse(reject_ids),
                ),
            }
            report.write(vals)

    @api.model
    def _customer_vetting_report_sale_orders(self):
        return self.env['sale.order'].search([
            ('service_request_id', '!=', False),
            ('state', 'in', ('sale', 'done')),
        ])

    @api.model
    def action_refresh_all(self):
        orders = self._customer_vetting_report_sale_orders()
        orders._sync_overall_customer_report_lines()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Overall customer report'),
            'res_model': 'overall.customer.report',
            'view_mode': 'list,form',
            'target': 'current',
        }
