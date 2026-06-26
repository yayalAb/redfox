# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class OverallCustomerReport(models.Model):
    _name = 'overall.customer.report'
    _description = 'Overall customer report'
    _order = 'partner_id, sale_order_id, id'
    _rec_name = 'display_name'

    sequence = fields.Integer(string='No.', readonly=True)
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
    order_date = fields.Datetime(
        string='Order date',
        related='sale_order_id.date_order',
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer name',
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
        string='Service product',
        related='sale_line_id.product_id',
        store=True,
        readonly=True,
    )
    product_name = fields.Char(
        string='Sales order products',
        compute='_compute_product_name',
        store=True,
    )
    grain_type = fields.Char(
        string='Product type',
        readonly=True,
        help='Raw material / grain type received from the customer.',
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
        string='Unit',
        compute='_compute_vetting_products',
        store=True,
    )
    total_received = fields.Float(
        string='Total received',
        digits='Product Unit of Measure',
        readonly=True,
    )
    total_delivered = fields.Float(
        string='Clean product issued',
        digits='Product Unit of Measure',
        readonly=True,
    )
    total_reject = fields.Float(
        string='Bran / waste issued',
        digits='Product Unit of Measure',
        readonly=True,
    )
    cleaned_remaining = fields.Float(
        string='Cleaned remaining',
        digits='Product Unit of Measure',
        readonly=True,
        help='Finished product produced but not yet delivered.',
    )
    estimated_bran_not_issued = fields.Float(
        string='Est. bran not issued',
        digits='Product Unit of Measure',
        readonly=True,
        help='By-product / reject produced but not yet delivered.',
    )
    issued_without_cleaning = fields.Float(
        string='Issued without cleaning',
        digits='Product Unit of Measure',
        readonly=True,
        help='Raw material delivered without manufacturing.',
    )
    uncleaned_in_warehouse = fields.Float(
        string='Uncleaned in warehouse',
        digits='Product Unit of Measure',
        readonly=True,
        help='Received raw material not yet consumed by manufacturing.',
    )
    difference = fields.Float(
        string='Difference',
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
                report.grain_type or report.product_name or '',
            ]
            report.display_name = ' / '.join(p for p in parts if p)

    def _vetting_service_line(self):
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

    def _round_qty(self, qty):
        self.ensure_one()
        if self.product_uom_id:
            return float_round(qty, precision_rounding=self.product_uom_id.rounding)
        return qty

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
        return self._round_qty(total)

    def _linked_done_mrp_productions(self):
        self.ensure_one()
        order = self.sale_order_id
        sol = self._vetting_service_line()
        mos = order._customer_vetting_done_receipt_mrp_productions()
        if not sol:
            return mos
        return mos.filtered(
            lambda mo: not mo._customer_vetting_service_sale_line()
            or mo._customer_vetting_service_sale_line() == sol
        )

    def _sum_mo_produced_qty(self, products):
        if not products:
            return 0.0
        product_set = set(products.ids if hasattr(products, 'ids') else products)
        if not product_set:
            return 0.0
        total = 0.0
        ref_uom = self.product_uom_id
        for mo in self._linked_done_mrp_productions():
            if mo.product_id.id in product_set and mo.qty_produced > 0:
                total += mo.product_uom_id._compute_quantity(
                    mo.qty_produced, ref_uom, rounding_method='HALF-UP'
                )
            for move in mo.move_byproduct_ids.filtered(lambda m: m.state == 'done'):
                if move.product_id.id in product_set and move.quantity > 0:
                    total += move.product_uom._compute_quantity(
                        move.quantity, ref_uom, rounding_method='HALF-UP'
                    )
        return self._round_qty(total)

    def _sum_raw_consumed_qty(self):
        self.ensure_one()
        raw = self.raw_product_id
        if not raw:
            return 0.0
        total = 0.0
        ref_uom = self.product_uom_id or raw.uom_id
        for mo in self._linked_done_mrp_productions():
            for move in mo.move_raw_ids.filtered(
                lambda m: m.state == 'done' and m.product_id == raw
            ):
                total += move.product_uom._compute_quantity(
                    move.quantity, ref_uom, rounding_method='HALF-UP'
                )
        return self._round_qty(total)

    def _recompute_quantities(self):
        Product = self.env['product.product']
        for report in self:
            order = report.sale_order_id
            raw, finished, _reject, _uom = report._vetting_products_for_line()
            receipts = order.product_detail_receipt_ids
            deliveries = order.customer_vetting_delivery_ids
            reject_products = Product.browse(report._reject_product_ids())

            total_received = report._sum_done_picking_qty(receipts, raw)
            total_delivered = report._sum_done_picking_qty(deliveries, finished)
            total_reject = report._sum_done_picking_qty(deliveries, reject_products)
            produced_finished = report._sum_mo_produced_qty(finished)
            produced_reject = report._sum_mo_produced_qty(reject_products)
            raw_consumed = report._sum_raw_consumed_qty()
            issued_without_cleaning = report._sum_done_picking_qty(deliveries, raw)

            cleaned_remaining = report._round_qty(
                max(0.0, produced_finished - total_delivered)
            )
            estimated_bran_not_issued = report._round_qty(
                max(0.0, produced_reject - total_reject)
            )
            uncleaned_in_warehouse = report._round_qty(
                max(0.0, total_received - raw_consumed - issued_without_cleaning)
            )
            difference = report._round_qty(
                total_received
                - total_delivered
                - total_reject
                - cleaned_remaining
                - estimated_bran_not_issued
                - issued_without_cleaning
                - uncleaned_in_warehouse
            )

            report.write({
                'grain_type': raw.display_name if raw else (report.product_name or ''),
                'total_received': total_received,
                'total_delivered': total_delivered,
                'total_reject': total_reject,
                'cleaned_remaining': cleaned_remaining,
                'estimated_bran_not_issued': estimated_bran_not_issued,
                'issued_without_cleaning': issued_without_cleaning,
                'uncleaned_in_warehouse': uncleaned_in_warehouse,
                'difference': difference,
            })

    @api.model
    def _assign_sequence_numbers(self):
        reports = self.search([], order='partner_id, sale_order_id, id')
        for index, report in enumerate(reports, start=1):
            if report.sequence != index:
                report.sequence = index

    @api.model
    def _customer_vetting_report_sale_orders(self):
        return self.env['sale.order'].search([
            ('service_request_id', '!=', False),
            ('state', 'in', ('sale', 'done')),
        ])

    def action_print_document(self):
        records = self
        if not records and self.env.context.get('active_ids'):
            records = self.browse(self.env.context['active_ids'])
        if not records:
            records = self.search([], order='partner_id, sale_order_id, id')
        if not records:
            raise UserError(
                _('No report lines to print. Open the overall customer report menu to build the report.')
            )
        records._assign_sequence_numbers()
        return self.env.ref(
            'customer_vetting.action_report_overall_customer_report'
        ).report_action(records)

    @api.model
    def action_refresh_all(self):
        orders = self._customer_vetting_report_sale_orders()
        orders._sync_overall_customer_report_lines()
        self._assign_sequence_numbers()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Overall customer report'),
            'res_model': 'overall.customer.report',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {'search_default_group_partner': 1},
        }
