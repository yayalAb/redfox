# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.tools import float_compare, float_round


class MfgDashboard(models.AbstractModel):
    _name = 'mfg.dashboard'
    _description = 'Manufacturing & Financial Executive Dashboard'

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    @api.model
    def get_dashboard_data(self, date_start=None, date_end=None, fiscal_year=None, year_over_year=False):
        start, end = self._parse_dates(date_start, date_end, fiscal_year)
        prev_start, prev_end = self._previous_period(start, end)

        payload = self._build_live_data(start, end, prev_start, prev_end)
        payload.update({
            'company_name': self.env.company.name,
            'subtitle': 'Executive Manufacturing Intelligence Report',
            'period_label': f'{fields.Date.to_string(start)} — {fields.Date.to_string(end)}',
            'date_start': fields.Date.to_string(start),
            'date_end': fields.Date.to_string(end),
            'use_live_data': True,
            'year_over_year': bool(year_over_year),
        })
        return payload

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _parse_dates(self, date_start, date_end, fiscal_year=None):
        today = fields.Date.context_today(self)
        if fiscal_year and str(fiscal_year).strip() not in ('', 'false', '0'):
            try:
                year = int(fiscal_year)
                return date(year, 1, 1), date(year, 12, 31)
            except (TypeError, ValueError):
                pass
        start = fields.Date.to_date(date_start) if date_start else today.replace(day=1)
        end = fields.Date.to_date(date_end) if date_end else today
        if start > end:
            start, end = end, start
        return start, end

    def _po_states(self):
        states = ['purchase', 'done']
        selection = dict(self.env['purchase.order']._fields['state'].selection)
        if 'sent' in selection:
            states.insert(0, 'sent')
        return tuple(states)

    def _so_states(self):
        return ('sale', 'done')

    def _mo_states_done(self):
        return ('done', 'to_close')

    def _internal_quant_domain(self):
        """Match internal stock for current company (via location, not quant.company_id)."""
        company = self.env.company.id
        return [
            ('location_id.usage', '=', 'internal'),
            '|',
            ('location_id.company_id', '=', False),
            ('location_id.company_id', '=', company),
        ]

    def _previous_period(self, start, end):
        days = (end - start).days + 1
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        return prev_start, prev_end

    def _dt_start(self, d):
        return fields.Datetime.to_datetime(datetime.combine(d, datetime.min.time()))

    def _dt_end(self, d):
        return fields.Datetime.to_datetime(datetime.combine(d, datetime.max.time()))

    def _fmt_money(self, amount):
        return float_round(amount or 0.0, precision_digits=2)

    def _fmt_qty(self, qty, uom_name=''):
        q = float_round(qty or 0.0, precision_digits=2)
        if uom_name:
            return f'{q:,.2f} {uom_name}'
        return f'{q:,.2f}'

    def _payment_status(self, total_bill, paid):
        remaining = (total_bill or 0) - (paid or 0)
        if float_compare(remaining, 0.0, precision_digits=2) <= 0:
            return 'Paid'
        if paid and paid > 0:
            return 'Partial'
        return 'Open'

    def _stock_status(self, available, minimum):
        if minimum and available < minimum:
            if available <= 0:
                return 'Critical'
            return 'Reorder Required'
        return 'Normal'

    def _product_bucket(self, product):
        """Classify product for stock KPIs: fg, raw, packaging, spare."""
        categ = (product.categ_id.complete_name or product.categ_id.name or '').lower()
        name = (product.display_name or '').lower()
        blob = f'{categ} {name}'
        if any(k in blob for k in ('spare', 'maintenance', 'bearing', 'belt', 'valve', 'blade')):
            return 'spare'
        if any(k in blob for k in ('packaging', 'pack', 'carton', 'film', 'bag', 'label')):
            return 'packaging'
        if any(k in blob for k in ('finished', 'fg ', '/ fg', 'macaroni', 'pasta', 'bravo', 'mondial')):
            return 'fg'
        if product.categ_id and product.categ_id.property_cost_method:
            pass
        # Manufactured / saleable finished goods
        if product.type == 'product' and not any(k in blob for k in ('raw', 'wheat', 'premix', 'fuel', 'nafta', 'grain')):
            if 'semi' not in blob and 'component' not in blob:
                # default storable non-RM to FG when no raw keyword
                if any(k in blob for k in ('raw', 'material', 'wheat', 'premix', 'fuel')):
                    return 'raw'
        if any(k in blob for k in ('raw', 'wheat', 'premix', 'fuel', 'nafta', 'grain', 'ingredient')):
            return 'raw'
        return 'raw'

    def _quant_value(self, quant):
        if 'value' in quant._fields and quant.value is not None:
            return quant.value
        qty = quant.quantity
        product = quant.product_id
        price = product.standard_price
        if hasattr(product, 'avg_cost') and product.avg_cost:
            price = product.avg_cost
        return qty * price

    def _trend_pct(self, current, previous):
        current = current or 0.0
        previous = previous or 0.0
        if not previous:
            return 0.0 if not current else 100.0
        return float_round((current - previous) / abs(previous) * 100.0, 2)

    def _empty_charts(self):
        empty = {'labels': ['No data'], 'datasets': [{'label': '', 'data': [0], 'backgroundColor': ['#e2e8f0']}]}
        return {
            'collection_outstanding': empty,
            'profitability': empty,
            'kpi_overview': empty,
        }

    # -------------------------------------------------------------------------
    # Live aggregation
    # -------------------------------------------------------------------------

    def _build_live_data(self, start, end, prev_start, prev_end):
        env = self.env
        company = env.company

        kpis = self._compute_kpis(start, end, prev_start, prev_end)
        procurement = self._compute_procurement(start, end)
        production_efficiency, rm_pm, byproducts = self._compute_manufacturing(start, end)
        fg_inventory = self._compute_fg_inventory(start, end)
        raw_material_stock, packaging_stock, spare_parts = self._compute_stock_tables(start, end)
        delivery_sales = self._compute_delivery_sales(start, end)
        customer_collections = self._compute_customer_collections(start, end)
        profitability = self._compute_profitability(start, end)

        charts = self._build_charts(kpis, customer_collections, profitability)

        return {
            'kpis': kpis['values'],
            'kpi_trends': kpis['trends'],
            'procurement': procurement,
            'production_efficiency': production_efficiency,
            'rm_pm_consumption': rm_pm,
            'byproduct_recovery': byproducts,
            'fg_inventory': fg_inventory,
            'raw_material_stock': raw_material_stock,
            'packaging_stock': packaging_stock,
            'spare_parts': spare_parts,
            'delivery_sales': delivery_sales,
            'customer_collections': customer_collections,
            'profitability': profitability,
            'charts': charts,
        }

    def _compute_kpis(self, start, end, prev_start, prev_end):
        env = self.env
        PurchaseOrder = env['purchase.order']
        MrpProduction = env['mrp.production']
        SaleOrder = env['sale.order']
        StockQuant = env['stock.quant']

        def purchase_total(d_start, d_end):
            pos = PurchaseOrder.search([
                ('state', 'in', self._po_states()),
                ('company_id', '=', env.company.id),
                ('date_order', '>=', self._dt_start(d_start)),
                ('date_order', '<=', self._dt_end(d_end)),
            ])
            return sum(pos.mapped('amount_total'))

        def production_cost(d_start, d_end):
            dt_s, dt_e = self._dt_start(d_start), self._dt_end(d_end)
            mos = MrpProduction.search([
                ('state', 'in', self._mo_states_done()),
                ('company_id', '=', env.company.id),
                '|', '|',
                '&', ('date_finished', '>=', dt_s), ('date_finished', '<=', dt_e),
                '&', ('date_start', '>=', dt_s), ('date_start', '<=', dt_e),
                '&', ('create_date', '>=', dt_s), ('create_date', '<=', dt_e),
            ])
            total = 0.0
            for mo in mos:
                for move in mo.move_raw_ids:
                    total += move.quantity * move.product_id.standard_price
            return total

        def sales_total(d_start, d_end):
            orders = SaleOrder.search([
                ('state', 'in', self._so_states()),
                ('company_id', '=', env.company.id),
                ('date_order', '>=', self._dt_start(d_start)),
                ('date_order', '<=', self._dt_end(d_end)),
            ])
            return sum(orders.mapped('amount_total'))

        def stock_values_by_bucket():
            buckets = {'fg': 0.0, 'raw': 0.0, 'packaging': 0.0, 'spare': 0.0}
            quants = StockQuant.search(self._internal_quant_domain())
            for quant in quants:
                if not quant.quantity:
                    continue
                bucket = self._product_bucket(quant.product_id)
                buckets[bucket] += self._quant_value(quant)
            return buckets

        buckets = stock_values_by_bucket()
        cur = {
            'total_purchase_value': purchase_total(start, end),
            'total_production_cost': production_cost(start, end),
            'total_sales_revenue': sales_total(start, end),
            'finished_goods_stock_value': buckets['fg'],
            'raw_material_stock_value': buckets['raw'],
            'packaging_stock_value': buckets['packaging'],
            'spare_part_stock_value': buckets['spare'],
        }
        prev = {
            'total_purchase_value': purchase_total(prev_start, prev_end),
            'total_production_cost': production_cost(prev_start, prev_end),
            'total_sales_revenue': sales_total(prev_start, prev_end),
        }
        trends = {k: self._trend_pct(cur.get(k), prev.get(k)) for k in prev}
        # Stock KPIs: point-in-time, no period trend
        for k in ('finished_goods_stock_value', 'raw_material_stock_value',
                  'packaging_stock_value', 'spare_part_stock_value'):
            trends[k] = 0.0

        # Raw numbers for the frontend (ETB formatting done in JS)
        values = {k: float_round(v, precision_digits=2) for k, v in cur.items()}
        return {'values': values, 'trends': trends}

    def _compute_procurement(self, start, end):
        PurchaseOrder = self.env['purchase.order']
        orders = PurchaseOrder.search([
            ('state', 'in', self._po_states()),
            ('company_id', '=', self.env.company.id),
            ('date_order', '>=', self._dt_start(start)),
            ('date_order', '<=', self._dt_end(end)),
        ], order='date_order desc', limit=100)
        rows = []
        for po in orders:
            done_pickings = po.picking_ids.filtered(lambda p: p.state == 'done')
            grn_qty = sum(done_pickings.move_ids_without_package.mapped('quantity'))
            grn_amount = 0.0
            for picking in done_pickings:
                for move in picking.move_ids_without_package:
                    grn_amount += move.quantity * (
                        move.price_unit or move.product_id.standard_price
                    )
            bills = po.invoice_ids.filtered(
                lambda m: m.move_type in ('in_invoice', 'in_refund') and m.state == 'posted'
            )
            bill_amount = sum(bills.mapped('amount_total'))
            paid = bill_amount - sum(bills.mapped('amount_residual'))
            rows.append({
                'po_no': po.name,
                'supplier': po.partner_id.display_name,
                'po_qty': sum(po.order_line.mapped('product_qty')),
                'po_amount': self._fmt_money(po.amount_total),
                'grn_qty': grn_qty,
                'grn_amount': self._fmt_money(grn_amount),
                'bill_amount': self._fmt_money(bill_amount),
                'paid_amount': self._fmt_money(paid),
                'remaining': self._fmt_money(bill_amount - paid),
                'payment_status': self._payment_status(bill_amount, paid),
            })
        return rows

    def _compute_manufacturing(self, start, end):
        MrpProduction = self.env['mrp.production']
        dt_s, dt_e = self._dt_start(start), self._dt_end(end)
        mos = MrpProduction.search([
            ('state', 'in', self._mo_states_done()),
            ('company_id', '=', self.env.company.id),
            '|', '|',
            '&', ('date_finished', '>=', dt_s), ('date_finished', '<=', dt_e),
            '&', ('date_start', '>=', dt_s), ('date_start', '<=', dt_e),
            '&', ('create_date', '>=', dt_s), ('create_date', '<=', dt_e),
        ], order='date_finished desc, id desc', limit=100)

        efficiency_rows = []
        consumption_rows = []
        byproduct_rows = []

        for mo in mos:
            planned = mo.product_qty or 0.0
            actual = mo.qty_produced or 0.0
            scrap_qty = sum(mo.scrap_ids.mapped('scrap_qty')) if mo.scrap_ids else 0.0
            efficiency = (actual / planned * 100.0) if planned else 0.0
            scrap_pct = (scrap_qty / planned * 100.0) if planned else 0.0

            byproduct_qty = 0.0
            for fin_move in mo.move_finished_ids:
                if fin_move.product_id != mo.product_id:
                    qty = fin_move.quantity
                    byproduct_qty += qty
                    byproduct_rows.append({
                        'product': mo.product_id.display_name,
                        'byproduct': fin_move.product_id.display_name,
                        'qty': self._fmt_qty(qty, fin_move.product_uom.name),
                        'estimated_value': self._fmt_money(
                            qty * fin_move.product_id.standard_price
                        ),
                    })

            byproduct_pct = (byproduct_qty / planned * 100.0) if planned else 0.0
            state_label = dict(
                self.env['mrp.production']._fields['state'].selection
            ).get(mo.state, mo.state)

            efficiency_rows.append({
                'mo_no': mo.name,
                'product': mo.product_id.display_name,
                'mo_qty': self._fmt_qty(planned, mo.product_uom_id.name),
                'actual_qty': self._fmt_qty(actual, mo.product_uom_id.name),
                'efficiency_pct': float_round(efficiency, 2),
                'byproduct_pct': float_round(byproduct_pct, 2),
                'scrap_pct': float_round(scrap_pct, 2),
                'status': state_label,
            })

            # RM/PM: BOM planned vs actual raw moves
            planned_map = defaultdict(float)
            if mo.bom_id:
                for line in mo.bom_id.bom_line_ids:
                    planned_map[line.product_id.id] += line.product_qty * (
                        planned / mo.bom_id.product_qty if mo.bom_id.product_qty else 1
                    )
            actual_map = defaultdict(float)
            for move in mo.move_raw_ids:
                actual_map[move.product_id.id] += move.quantity

            product_ids = set(planned_map) | set(actual_map)
            for pid in product_ids:
                product = self.env['product.product'].browse(pid)
                p_qty = planned_map.get(pid, 0.0)
                a_qty = actual_map.get(pid, 0.0)
                variance = a_qty - p_qty
                cost_impact = variance * product.standard_price
                sign = '+' if variance >= 0 else ''
                consumption_rows.append({
                    'product': mo.product_id.display_name,
                    'planned': self._fmt_qty(p_qty, product.uom_id.name),
                    'actual': self._fmt_qty(a_qty, product.uom_id.name),
                    'variance': f'{sign}{float_round(variance, 2)} {product.uom_id.name}',
                    'cost_impact': self._fmt_money(cost_impact),
                })

        return efficiency_rows, consumption_rows, byproduct_rows

    def _compute_fg_inventory(self, start, end):
        """FG products: stock summary using moves in period + current quants."""
        StockMove = self.env['stock.move']
        StockQuant = self.env['stock.quant']
        MrpProduction = self.env['mrp.production']

        products = self.env['product.product'].search([
            ('type', '=', 'product'),
            ('company_id', 'in', (False, self.env.company.id)),
        ])
        fg_products = products.filtered(lambda p: self._product_bucket(p) == 'fg')

        rows = []
        dt_s, dt_e = self._dt_start(start), self._dt_end(end)
        for product in fg_products[:80]:
            quants = StockQuant.search(
                self._internal_quant_domain() + [('product_id', '=', product.id)]
            )
            ending_qty = sum(quants.mapped('quantity'))
            stock_value = sum(self._quant_value(q) for q in quants)
            if not ending_qty and not stock_value:
                continue

            produced = sum(MrpProduction.search([
                ('product_id', '=', product.id),
                ('state', 'in', self._mo_states_done()),
                '|', '|',
                '&', ('date_finished', '>=', dt_s), ('date_finished', '<=', dt_e),
                '&', ('date_start', '>=', dt_s), ('date_start', '<=', dt_e),
                '&', ('create_date', '>=', dt_s), ('create_date', '<=', dt_e),
            ]).mapped('qty_produced'))

            sold_moves = StockMove.search([
                ('product_id', '=', product.id),
                ('state', '=', 'done'),
                ('location_dest_id.usage', '=', 'customer'),
                ('date', '>=', self._dt_start(start)),
                ('date', '<=', self._dt_end(end)),
            ])
            sold = sum(sold_moves.mapped('quantity'))

            opening_qty = ending_qty - produced + sold
            uom = product.uom_id.name

            rows.append({
                'product': product.display_name,
                'opening': self._fmt_qty(max(opening_qty, 0), uom),
                'produced': self._fmt_qty(produced, uom),
                'sold': self._fmt_qty(sold, uom),
                'ending': self._fmt_qty(ending_qty, uom),
                'stock_value': self._fmt_money(stock_value),
                '_sort_value': stock_value,
            })
        rows.sort(key=lambda r: r['_sort_value'], reverse=True)
        for row in rows:
            row.pop('_sort_value', None)
        return rows

    def _compute_stock_tables(self, start, end):
        StockQuant = self.env['stock.quant']
        StockMove = self.env['stock.move']

        raw_rows, pack_rows, spare_rows = [], [], []
        quants = StockQuant.search(self._internal_quant_domain())

        product_data = defaultdict(lambda: {
            'available': 0.0, 'reserved': 0.0, 'value': 0.0,
        })
        for quant in quants:
            if not quant.quantity:
                continue
            pid = quant.product_id.id
            product_data[pid]['available'] += quant.quantity
            product_data[pid]['reserved'] += quant.reserved_quantity
            product_data[pid]['value'] += self._quant_value(quant)

        consumption_domain = [
            ('state', '=', 'done'),
            ('date', '>=', self._dt_start(start)),
            ('date', '<=', self._dt_end(end)),
        ]

        for pid, data in product_data.items():
            product = self.env['product.product'].browse(pid)
            bucket = self._product_bucket(product)
            if bucket == 'fg' or data['available'] <= 0:
                continue

            available = data['available']
            reserved = data['reserved']
            free = available - reserved
            value = data['value']
            uom = product.uom_id.name

            consumed_moves = StockMove.search(
                consumption_domain + [('product_id', '=', pid)]
            )
            consumption = sum(
                m.quantity for m in consumed_moves
                if m.location_dest_id.usage in ('production', 'customer')
            )

            if bucket == 'packaging':
                pack_rows.append({
                    'material': product.display_name,
                    'available': self._fmt_qty(available, uom),
                    'consumption': self._fmt_qty(consumption, uom),
                    'remaining': self._fmt_qty(free, uom),
                    'stock_value': self._fmt_money(value),
                    '_sort_value': value,
                })
            elif bucket == 'spare':
                minimum = 0.0
                if 'reordering_min_qty' in product._fields:
                    minimum = product.reordering_min_qty or 0.0
                machine = ''
                if 'equipment_id' in product._fields and product.equipment_id:
                    machine = product.equipment_id.display_name
                spare_rows.append({
                    'part': product.display_name,
                    'machine': machine,
                    'available': self._fmt_qty(available, uom),
                    'minimum': self._fmt_qty(minimum, uom) if minimum else '—',
                    'status': self._stock_status(free, minimum),
                    'stock_value': self._fmt_money(value),
                    '_sort_value': value,
                })
            else:
                raw_rows.append({
                    'material': product.display_name,
                    'available': self._fmt_qty(available, uom),
                    'reserved': self._fmt_qty(reserved, uom),
                    'free_stock': self._fmt_qty(free, uom),
                    'stock_value': self._fmt_money(value),
                    '_sort_value': value,
                })

        for lst in (raw_rows, pack_rows, spare_rows):
            lst.sort(key=lambda r: r['_sort_value'], reverse=True)
            for row in lst:
                row.pop('_sort_value', None)
        return raw_rows[:50], pack_rows[:50], spare_rows[:50]

    def _compute_delivery_sales(self, start, end):
        Picking = self.env['stock.picking']
        pickings = Picking.search([
            ('picking_type_id.code', '=', 'outgoing'),
            ('state', '=', 'done'),
            ('company_id', '=', self.env.company.id),
            ('date_done', '>=', self._dt_start(start)),
            ('date_done', '<=', self._dt_end(end)),
        ], order='date_done desc', limit=100)

        rows = []
        for picking in pickings:
            customer = picking.partner_id.display_name or (
                picking.sale_id.partner_id.display_name if picking.sale_id else ''
            )
            for move in picking.move_ids_without_package:
                invoiced_qty = move.quantity
                if picking.sale_id:
                    sol = picking.sale_id.order_line.filtered(
                        lambda l: l.product_id == move.product_id
                    )
                    if sol:
                        invoiced_qty = sum(sol.mapped('qty_invoiced'))
                rows.append({
                    'do_no': picking.name,
                    'customer': customer,
                    'product': move.product_id.display_name,
                    'delivered_qty': self._fmt_qty(move.quantity, move.product_uom.name),
                    'invoiced_qty': self._fmt_qty(invoiced_qty, move.product_uom.name),
                    'delivery_status': 'Delivered',
                })
        return rows

    def _compute_customer_collections(self, start, end):
        AccountMove = self.env['account.move']
        invoices = AccountMove.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('company_id', '=', self.env.company.id),
            ('invoice_date', '>=', start),
            ('invoice_date', '<=', end),
        ], order='invoice_date desc', limit=100)

        rows = []
        for inv in invoices:
            collected = inv.amount_total - inv.amount_residual
            remaining = inv.amount_residual
            rows.append({
                'customer': inv.partner_id.display_name,
                'invoice_amount': self._fmt_money(inv.amount_total),
                'collected_amount': self._fmt_money(collected),
                'remaining': self._fmt_money(remaining),
                'remaining_raw': remaining,
                'collection_status': self._payment_status(inv.amount_total, collected),
            })
        return rows

    def _compute_profitability(self, start, end):
        SaleOrder = self.env['sale.order']
        MrpProduction = self.env['mrp.production']

        orders = SaleOrder.search([
            ('state', 'in', self._so_states()),
            ('company_id', '=', self.env.company.id),
            ('date_order', '>=', self._dt_start(start)),
            ('date_order', '<=', self._dt_end(end)),
        ])

        revenue_by_product = defaultdict(float)
        for order in orders:
            for line in order.order_line.filtered(lambda l: not l.display_type):
                revenue_by_product[line.product_id.id] += line.price_subtotal

        cost_by_product = defaultdict(float)
        dt_s, dt_e = self._dt_start(start), self._dt_end(end)
        mos = MrpProduction.search([
            ('state', 'in', self._mo_states_done()),
            ('company_id', '=', self.env.company.id),
            '|', '|',
            '&', ('date_finished', '>=', dt_s), ('date_finished', '<=', dt_e),
            '&', ('date_start', '>=', dt_s), ('date_start', '<=', dt_e),
            '&', ('create_date', '>=', dt_s), ('create_date', '<=', dt_e),
        ])
        for mo in mos:
            cost = sum(
                m.quantity * m.product_id.standard_price for m in mo.move_raw_ids
            )
            cost_by_product[mo.product_id.id] += cost

        product_ids = set(revenue_by_product) | set(cost_by_product)
        rows = []
        for pid in product_ids:
            product = self.env['product.product'].browse(pid)
            revenue = revenue_by_product.get(pid, 0.0)
            cost = cost_by_product.get(pid, 0.0)
            profit = revenue - cost
            margin = (profit / revenue * 100.0) if revenue else 0.0
            rows.append({
                'product': product.display_name,
                'revenue': self._fmt_money(revenue),
                'production_cost': self._fmt_money(cost),
                'gross_profit': self._fmt_money(profit),
                'gross_profit_raw': profit,
                'profit_margin': float_round(margin, 1),
            })
        rows.sort(key=lambda r: r.get('gross_profit_raw', 0), reverse=True)
        return rows[:30]

    def _build_charts(self, kpis, collections, profitability):
        kpi_labels = [
            'Purchase', 'Production', 'Sales', 'FG Stock',
            'RM Stock', 'Packaging', 'Spare Parts',
        ]
        kpi_keys = [
            'total_purchase_value', 'total_production_cost', 'total_sales_revenue',
            'finished_goods_stock_value', 'raw_material_stock_value',
            'packaging_stock_value', 'spare_part_stock_value',
        ]
        kpi_data = [float(kpis['values'].get(k, 0) or 0) for k in kpi_keys]

        coll_with_balance = [
            c for c in collections
            if float(c.get('remaining', 0) or 0) > 0
        ][:8]
        if coll_with_balance:
            coll_labels = [c['customer'] for c in coll_with_balance]
            coll_data = [float(c.get('remaining_raw', 0) or 0) for c in coll_with_balance]
        else:
            coll_labels = ['No outstanding']
            coll_data = [0]

        profit_rows = profitability[:8]
        if profit_rows:
            profit_labels = [p['product'] for p in profit_rows]
            profit_data = [float(p.get('gross_profit_raw', 0) or 0) for p in profit_rows]
        else:
            profit_labels = ['No data']
            profit_data = [0]

        colors = [
            'rgba(30, 58, 95, 0.75)', 'rgba(212, 160, 18, 0.75)',
            'rgba(54, 162, 235, 0.75)', 'rgba(75, 192, 192, 0.75)',
            'rgba(255, 159, 64, 0.75)', 'rgba(153, 102, 255, 0.75)',
            'rgba(255, 99, 132, 0.75)',
        ]
        return {
            'kpi_overview': {
                'labels': kpi_labels,
                'datasets': [{
                    'label': 'Value (ETB)',
                    'data': kpi_data,
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': 1,
                }],
            },
            'collection_outstanding': {
                'labels': coll_labels,
                'datasets': [{
                    'label': 'Outstanding (ETB)',
                    'data': coll_data,
                    'backgroundColor': colors[:len(coll_data)],
                }],
            },
            'profitability': {
                'labels': profit_labels,
                'datasets': [{
                    'label': 'Gross Profit (ETB)',
                    'data': profit_data,
                    'backgroundColor': 'rgba(30, 58, 95, 0.7)',
                    'borderColor': 'rgba(30, 58, 95, 1)',
                    'borderWidth': 1,
                }],
            },
        }
