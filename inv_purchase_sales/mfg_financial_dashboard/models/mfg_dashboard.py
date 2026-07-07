# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import date, datetime, timedelta
import re

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.tools import float_compare, float_round


class MfgDashboard(models.AbstractModel):
    _name = 'mfg.dashboard'
    _description = 'Manufacturing & Financial Executive Dashboard'

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    @api.model
    def get_dashboard_data(
        self,
        date_start=None,
        date_end=None,
        fiscal_year=None,
        year_over_year=False,
        date_range=None,
    ):
        """Aggregate live ERP data for the executive dashboard (read-only)."""
        dashboard = self.sudo().with_company(self.env.company)
        range_key = date_range or 'this_year_ytd'
        if fiscal_year and str(fiscal_year).strip() not in ('', 'false', '0'):
            start, end = dashboard._parse_dates(date_start, date_end, fiscal_year)
            range_key = 'custom'
        else:
            start, end, range_key = dashboard._resolve_date_range(
                range_key, date_start, date_end,
            )
        prev_start, prev_end = dashboard._comparison_period(start, end, range_key)
        comparison_label = dashboard._comparison_label(range_key)

        payload = dashboard._build_live_data(
            start, end, prev_start, prev_end, range_key,
        )
        payload.update({
            'company_name': self.env.company.name,
            'subtitle': 'Executive Manufacturing Intelligence Report',
            'period_label': f'{fields.Date.to_string(start)} — {fields.Date.to_string(end)}',
            'date_start': fields.Date.to_string(start),
            'date_end': fields.Date.to_string(end),
            'date_range': range_key,
            'comparison_label': comparison_label,
            'comparison_period_label': (
                f'{fields.Date.to_string(prev_start)} — {fields.Date.to_string(prev_end)}'
            ),
            'use_live_data': True,
            'year_over_year': bool(year_over_year),
        })
        return payload

    @api.model
    def open_stock_movement_detail(
        self, product_id, warehouse_id, date_start=None, date_end=None,
    ):
        """Open done stock moves for a dashboard summary line."""
        dashboard = self.sudo().with_company(self.env.company)
        start, end = dashboard._parse_dates(date_start, date_end)
        start_dt, end_dt = dashboard._dt_start(start), dashboard._dt_end(end)
        product = self.env['product.product'].browse(int(product_id))
        warehouse = self.env['stock.warehouse'].browse(int(warehouse_id))
        if not product.exists() or not warehouse.exists():
            return False
        title = _('Stock Movements — %s / %s') % (
            product.display_name,
            self._warehouse_display_name(warehouse.name),
        )
        return dashboard._act_window_action(
            title,
            'stock.move',
            [
                ('state', '=', 'done'),
                ('company_id', '=', self.env.company.id),
                ('product_id', '=', product.id),
                ('date', '>=', fields.Datetime.to_string(start_dt)),
                ('date', '<=', fields.Datetime.to_string(end_dt)),
                '|',
                ('location_id.warehouse_id', '=', warehouse.id),
                ('location_dest_id.warehouse_id', '=', warehouse.id),
            ],
            context={'create': False},
        )

    def _act_window_action(self, name, res_model, domain, view_mode='list,form', context=None):
        modes = [mode.strip() for mode in view_mode.split(',') if mode.strip()]
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': res_model,
            'view_mode': ','.join(modes),
            'views': [[False, mode] for mode in modes],
            'domain': domain,
            'target': 'current',
            'context': context or {},
        }

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

    def _resolve_date_range(self, range_key, date_start=None, date_end=None):
        """Return (start, end, range_key) for a named or custom dashboard period."""
        key = (range_key or 'this_year_ytd').strip()
        if key == 'custom':
            return *self._parse_dates(date_start, date_end), 'custom'
        return *self._preset_date_bounds(key), key

    def _preset_date_bounds(self, range_key):
        """Return (start, end) for a named dashboard period."""
        today = fields.Date.context_today(self)
        company = self.env.company

        if range_key == 'today':
            return today, today
        if range_key == 'yesterday':
            day = today - timedelta(days=1)
            return day, day
        if range_key == 'last_7_days':
            return today - timedelta(days=6), today
        if range_key == 'last_30_days':
            return today - timedelta(days=29), today
        if range_key == 'this_week':
            week_start = today - timedelta(days=today.weekday())
            return week_start, today
        if range_key == 'last_week':
            this_week_start = today - timedelta(days=today.weekday())
            last_week_start = this_week_start - timedelta(days=7)
            last_week_end = last_week_start + timedelta(days=6)
            return last_week_start, last_week_end
        if range_key == 'this_month_mtd':
            return today.replace(day=1), today
        if range_key == 'last_month':
            first_this_month = today.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            return last_month_end.replace(day=1), last_month_end
        if range_key == 'this_quarter_qtd':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            return today.replace(month=quarter_start_month, day=1), today
        if range_key == 'last_quarter':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            this_quarter_start = today.replace(month=quarter_start_month, day=1)
            last_quarter_end = this_quarter_start - timedelta(days=1)
            last_quarter_start_month = ((last_quarter_end.month - 1) // 3) * 3 + 1
            last_quarter_start = last_quarter_end.replace(
                month=last_quarter_start_month, day=1,
            )
            return last_quarter_start, last_quarter_end
        if range_key == 'this_year_ytd':
            fiscal = company.compute_fiscalyear_dates(today)
            return fiscal['date_from'], today
        if range_key == 'last_year':
            fiscal = company.compute_fiscalyear_dates(today)
            previous_ref = fiscal['date_from'] - timedelta(days=1)
            previous_fiscal = company.compute_fiscalyear_dates(previous_ref)
            return previous_fiscal['date_from'], previous_fiscal['date_to']
        return self._parse_dates(None, None)

    def _comparison_period(self, start, end, range_key=None):
        """Previous period aligned with the selected range semantics."""
        key = range_key or 'custom'
        if key in ('this_year_ytd', 'last_year'):
            return start + relativedelta(years=-1), end + relativedelta(years=-1)
        if key in ('this_month_mtd', 'last_month'):
            return start + relativedelta(months=-1), end + relativedelta(months=-1)
        if key in ('this_quarter_qtd', 'last_quarter'):
            return start + relativedelta(months=-3), end + relativedelta(months=-3)
        if key == 'today':
            day = start - timedelta(days=1)
            return day, day
        if key == 'yesterday':
            day = start - timedelta(days=1)
            return day, day
        if key in ('this_week', 'last_week'):
            return start + relativedelta(weeks=-1), end + relativedelta(weeks=-1)
        return self._previous_period(start, end)

    def _comparison_label(self, range_key):
        labels = {
            'today': 'vs yesterday',
            'yesterday': 'vs prior day',
            'last_7_days': 'vs previous 7 days',
            'this_week': 'vs last week',
            'last_week': 'vs prior week',
            'last_30_days': 'vs previous 30 days',
            'this_month_mtd': 'vs same period last month',
            'last_month': 'vs prior month',
            'this_quarter_qtd': 'vs same period last quarter',
            'last_quarter': 'vs prior quarter',
            'this_year_ytd': 'vs same period last year',
            'last_year': 'vs prior year',
            'custom': 'vs previous period',
        }
        return labels.get(range_key, 'vs previous period')

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
        """Internal on-hand stock for the active company."""
        company = self.env.company
        return [
            ('location_id.usage', '=', 'internal'),
            '|',
            ('location_id.company_id', '=', False),
            ('location_id.company_id', '=', company.id),
        ]

    def _company_warehouses(self):
        return self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id),
        ])

    def _warehouse_english_label(self, name):
        """Use only the English part of bilingual warehouse names."""
        if not name:
            return ''
        text = str(name).strip()
        if '/' in text:
            text = text.split('/', 1)[0]
        elif '(' in text:
            text = text.split('(', 1)[0]
        text = re.sub(r'[\u1200-\u137F]+', '', text).strip(' /-')
        return text.lower()

    def _warehouse_display_name(self, name):
        label = self._warehouse_english_label(name)
        if label:
            return label.title()
        return (name or '').strip()

    def _location_warehouse(self, location, warehouses=None):
        if not location:
            return self.env['stock.warehouse']
        warehouse = location.warehouse_id
        if warehouse:
            return warehouse
        warehouses = warehouses or self._company_warehouses()
        parent_path = location.parent_path or ''
        if not parent_path:
            return self.env['stock.warehouse']
        padded = f'/{parent_path}'
        for wh in warehouses:
            root = wh.view_location_id
            if root and f'/{root.id}/' in padded:
                return wh
        return self.env['stock.warehouse']

    def _warehouse_bucket(self, warehouse):
        """Map warehouse to stock KPI bucket using the English name."""
        if not warehouse:
            return None
        label = self._warehouse_english_label(warehouse.name)
        if not label:
            return None
        if any(k in label for k in ('sparepart', 'spare part', 'spare')):
            return 'spare'
        if 'raw material' in label or label.startswith('raw '):
            return 'raw'
        if any(k in label for k in ('finished', 'finshed', 'finish good', 'finished good')):
            return 'fg'
        if any(k in label for k in ('stationery', 'consumable', 'packaging')):
            return 'packaging'
        if any(k in label for k in ('main store', 'ho-main', 'ho main')):
            return 'raw'
        return None

    def _quant_stock_bucket(self, quant, warehouses=None):
        warehouse = self._location_warehouse(quant.location_id, warehouses)
        bucket = self._warehouse_bucket(warehouse)
        if bucket:
            return bucket
        return self._product_bucket(quant.product_id)

    def _previous_period(self, start, end):
        days = (end - start).days + 1
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        return prev_start, prev_end

    def _dt_start(self, d):
        return fields.Datetime.to_datetime(datetime.combine(d, datetime.min.time()))

    def _dt_end(self, d):
        return fields.Datetime.to_datetime(datetime.combine(d, datetime.max.time()))

    def _company_domain(self, model_name):
        """Restrict to the active company."""
        model = self.env[model_name]
        if 'company_id' not in model._fields:
            return []
        return [('company_id', '=', self.env.company.id)]

    def _mo_period_domain(self, start, end):
        """Manufacturing orders that belong to the selected period."""
        dt_s, dt_e = self._dt_start(start), self._dt_end(end)
        return [
            ('state', 'in', self._mo_states_done()),
            *self._company_domain('mrp.production'),
            '|', '|',
            '&', ('date_finished', '>=', dt_s), ('date_finished', '<=', dt_e),
            '&', ('date_start', '>=', dt_s), ('date_start', '<=', dt_e),
            '&', ('create_date', '>=', dt_s), ('create_date', '<=', dt_e),
        ]

    def _stock_move_sql_columns(self):
        """Cached stock_move column list (avoids ORM fetch on broken custom fields)."""
        cache = getattr(MfgDashboard, '_stock_move_col_cache', None)
        dbname = self.env.cr.dbname
        if not cache or cache[0] != dbname:
            self.env.cr.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'stock_move'
                  AND table_schema = current_schema()
            """)
            cols = {r[0] for r in self.env.cr.fetchall()}
            MfgDashboard._stock_move_col_cache = (dbname, cols)
        return MfgDashboard._stock_move_col_cache[1]

    def _stock_move_has_column(self, column_name):
        return column_name in self._stock_move_sql_columns()

    def _sum_stock_move_qty(self, move_ids):
        if not move_ids:
            return 0.0
        self.env.cr.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM stock_move WHERE id IN %s",
            (tuple(move_ids),),
        )
        return self.env.cr.fetchone()[0] or 0.0

    def _stock_move_qty_by_product(self, move_ids):
        if not move_ids:
            return {}
        self.env.cr.execute(
            """
            SELECT product_id, COALESCE(SUM(quantity), 0)
            FROM stock_move
            WHERE id IN %s
            GROUP BY product_id
            """,
            (tuple(move_ids),),
        )
        return {row[0]: row[1] for row in self.env.cr.fetchall()}

    def _sum_stock_move_qty_dest(self, move_ids, usages):
        if not move_ids:
            return 0.0
        self.env.cr.execute(
            """
            SELECT COALESCE(SUM(sm.quantity), 0)
            FROM stock_move sm
            JOIN stock_location sl ON sm.location_dest_id = sl.id
            WHERE sm.id IN %s AND sl.usage IN %s
            """,
            (tuple(move_ids), tuple(usages)),
        )
        return self.env.cr.fetchone()[0] or 0.0

    def _product_standard_price_map(self, product_ids):
        """Read standard_price via ORM (company_dependent jsonb in PostgreSQL)."""
        if not product_ids:
            return {}
        products = self.env['product.product'].with_company(self.env.company).browse(
            list(product_ids)
        )
        return {p.id: float(p.standard_price or 0.0) for p in products}

    def _stock_move_cost_total(self, move_ids):
        if not move_ids:
            return 0.0
        if self._stock_move_has_column('value'):
            self.env.cr.execute(
                """
                SELECT COALESCE(SUM(ABS(value)), 0)
                FROM stock_move
                WHERE id IN %s AND COALESCE(value, 0) != 0
                """,
                (tuple(move_ids),),
            )
            val = self.env.cr.fetchone()[0] or 0.0
            if val:
                return val
        self.env.cr.execute(
            """
            SELECT product_id, COALESCE(quantity, 0)
            FROM stock_move
            WHERE id IN %s
            """,
            (tuple(move_ids),),
        )
        rows = self.env.cr.fetchall()
        price_map = self._product_standard_price_map({r[0] for r in rows})
        return sum(
            (qty or 0.0) * price_map.get(product_id, 0.0)
            for product_id, qty in rows
        )

    def _mo_raw_move_ids(self, mo_ids):
        if not mo_ids or not self._stock_move_has_column('raw_material_production_id'):
            return []
        self.env.cr.execute(
            """
            SELECT id FROM stock_move
            WHERE raw_material_production_id IN %s
            """,
            (tuple(mo_ids),),
        )
        return [r[0] for r in self.env.cr.fetchall()]

    def _stock_move_lines_data(self, move_ids):
        """Read move lines via SQL on numeric columns only; labels via ORM."""
        if not move_ids:
            return []
        select_parts = ['sm.id', 'sm.quantity', 'sm.product_id']
        has_price_unit = self._stock_move_has_column('price_unit')
        has_product_uom = self._stock_move_has_column('product_uom')
        if has_price_unit:
            select_parts.append('sm.price_unit')
        if has_product_uom:
            select_parts.append('sm.product_uom')
        self.env.cr.execute(
            f"""
            SELECT {', '.join(select_parts)}
            FROM stock_move sm
            WHERE sm.id IN %s
            """,
            (tuple(move_ids),),
        )
        raw_rows = self.env.cr.fetchall()
        product_ids = set()
        uom_ids = set()
        parsed = []
        for row in raw_rows:
            move_id, qty, product_id = row[0], row[1] or 0.0, row[2]
            idx = 3
            price_unit = 0.0
            uom_id = False
            if has_price_unit:
                price_unit = float(row[idx] or 0.0)
                idx += 1
            if has_product_uom:
                uom_id = row[idx] or False
                if uom_id:
                    uom_ids.add(uom_id)
            product_ids.add(product_id)
            parsed.append({
                'id': move_id,
                'quantity': qty,
                'product_id': product_id,
                'price_unit': price_unit,
                'uom_id': uom_id,
            })

        price_map = self._product_standard_price_map(product_ids)
        products = self.env['product.product'].browse(list(product_ids))
        product_names = {p.id: p.display_name for p in products}
        uom_names = {}
        if uom_ids:
            for uom in self.env['uom.uom'].browse(list(uom_ids)):
                uom_names[uom.id] = uom.name

        rows = []
        for item in parsed:
            pid = item['product_id']
            uom_id = item['uom_id']
            product = products.browse(pid)
            rows.append({
                'id': item['id'],
                'quantity': item['quantity'],
                'product_id': pid,
                'product_name': product_names.get(pid, product.display_name),
                'price_unit': item['price_unit'],
                'standard_price': price_map.get(pid, 0.0),
                'uom_name': uom_names.get(uom_id) or product.uom_id.name or '',
            })
        return rows

    def _product_sold_qty_sql(self, product_id, dt_start, dt_end):
        self.env.cr.execute(
            """
            SELECT COALESCE(SUM(sm.quantity), 0)
            FROM stock_move sm
            JOIN stock_location sl ON sm.location_dest_id = sl.id
            WHERE sm.product_id = %s
              AND sm.state = 'done'
              AND sl.usage = 'customer'
              AND sm.date >= %s
              AND sm.date <= %s
            """,
            (product_id, dt_start, dt_end),
        )
        return self.env.cr.fetchone()[0] or 0.0

    def _fmt_money(self, amount):
        return float_round(amount or 0.0, precision_digits=2)

    def _fmt_qty(self, qty, uom_name=''):
        q = float_round(qty or 0.0, precision_digits=2)
        if uom_name:
            return f'{q:,.2f} {uom_name}'
        return f'{q:,.2f}'

    def _payment_status(self, total_bill, paid):
        total_bill = total_bill or 0.0
        paid = paid or 0.0
        if float_compare(total_bill, 0.0, precision_digits=2) <= 0:
            return 'Not Billed'
        remaining = total_bill - paid
        if float_compare(remaining, 0.0, precision_digits=2) <= 0:
            return 'Paid'
        if float_compare(paid, 0.0, precision_digits=2) > 0:
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
        if any(k in blob for k in ('packaging', 'pack', 'carton', 'film', 'bag', 'label', 'wrapper')):
            return 'packaging'
        if any(k in blob for k in (
            'finished', 'finish goods', 'finished goods', 'fg ', '/fg', '-fg-',
            'macaroni', 'pasta', 'bravo', 'mondial', 'end product',
        )):
            return 'fg'
        if any(k in blob for k in ('raw', 'wheat', 'premix', 'fuel', 'nafta', 'grain', 'ingredient', 'flour')):
            return 'raw'
        # Saleable / manufactured storable products default to FG
        if product.type == 'product':
            if getattr(product, 'bom_count', 0) or 'semi' in blob:
                return 'fg'
            if product.sale_ok and 'component' not in blob:
                return 'fg'
        return 'raw'

    def _quant_value(self, quant):
        qty = quant.quantity or 0.0
        if not qty:
            return 0.0
        if 'value' in quant._fields and quant.value:
            val = abs(quant.value)
            if val:
                return val
        product = quant.product_id.with_company(self.env.company)
        price = product.standard_price or 0.0
        if 'avg_cost' in product._fields and product.avg_cost:
            price = product.avg_cost
        if not price:
            price = product.list_price or 0.0
        return abs(qty * price)

    def _posted_customer_invoices(self, start, end):
        return self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            *self._company_domain('account.move'),
            ('invoice_date', '>=', start),
            ('invoice_date', '<=', end),
        ])

    def _posted_vendor_bills(self, start, end):
        return self.env['account.move'].search([
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            *self._company_domain('account.move'),
            ('invoice_date', '>=', start),
            ('invoice_date', '<=', end),
        ])

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

    def _build_live_data(self, start, end, prev_start, prev_end, range_key='custom'):
        env = self.env
        company = env.company

        kpis = self._compute_kpis(start, end, prev_start, prev_end, range_key)
        workflow_kpis = self._compute_workflow_kpis(start, end, prev_start, prev_end)
        procurement = self._compute_procurement(start, end)
        production_efficiency, rm_pm, byproducts = self._compute_manufacturing(start, end)
        fg_inventory = self._compute_fg_inventory(start, end)
        raw_material_stock, packaging_stock, spare_parts = self._compute_stock_tables(start, end)
        delivery_sales = self._compute_delivery_sales(start, end)
        customer_collections = self._compute_customer_collections(start, end)
        partner_ledger_data = self._compute_partner_ledger(start, end)
        profitability = self._compute_profitability(start, end)
        stock_movements = self._stock_movement_rows(start, end)

        charts = self._build_charts(kpis, customer_collections, profitability)

        return {
            'kpis': kpis['values'],
            'kpi_trends': kpis['trends'],
            'workflow_kpis': workflow_kpis,
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
            'partner_ledger': partner_ledger_data['lines'],
            'partner_ledger_partners': partner_ledger_data['partners'],
            'partner_ledger_partner_totals': partner_ledger_data['partner_totals'],
            'partner_ledger_grand_total': partner_ledger_data['grand_total'],
            'profitability': profitability,
            'stock_movements': stock_movements,
            'stock_movement_summary': self._stock_movement_summary(stock_movements),
            'charts': charts,
        }

    def _stock_movement_rows(self, start, end):
        """Summarize done stock moves by product and warehouse for the period."""
        company = self.env.company
        start_dt, end_dt = self._dt_start(start), self._dt_end(end)
        moves = self.env['stock.move'].search([
            ('state', '=', 'done'),
            ('company_id', '=', company.id),
            ('product_id', '!=', False),
            ('date', '>=', start_dt),
            ('date', '<=', end_dt),
        ])
        warehouses = self._company_warehouses()
        aggregated = defaultdict(lambda: {'total_in': 0.0, 'total_out': 0.0})
        for move in moves:
            qty = move.quantity or getattr(move, 'product_uom_qty', 0.0) or 0.0
            product = move.product_id
            if move.location_dest_id.usage == 'internal':
                warehouse = self._location_warehouse(move.location_dest_id, warehouses)
                if warehouse:
                    key = (product.id, warehouse.id)
                    aggregated[key]['total_in'] += qty
            if move.location_id.usage == 'internal':
                warehouse = self._location_warehouse(move.location_id, warehouses)
                if warehouse:
                    key = (product.id, warehouse.id)
                    aggregated[key]['total_out'] += qty

        products = self.env['product.product'].browse({k[0] for k in aggregated})
        warehouses = self.env['stock.warehouse'].browse({k[1] for k in aggregated})
        product_by_id = {p.id: p for p in products}
        warehouse_by_id = {w.id: w for w in warehouses}

        rows = []
        for (product_id, warehouse_id), data in aggregated.items():
            product = product_by_id.get(product_id)
            warehouse = warehouse_by_id.get(warehouse_id)
            if not product or not warehouse:
                continue
            total_in = float_round(data['total_in'], 2)
            total_out = float_round(data['total_out'], 2)
            rows.append({
                'id': f'{product_id}_{warehouse_id}',
                'product_id': product_id,
                'warehouse_id': warehouse_id,
                'product': product.display_name,
                'product_reference': product.default_code or '—',
                'warehouse': self._warehouse_display_name(warehouse.name),
                'total_in': total_in,
                'total_out': total_out,
                'balance': float_round(total_in - total_out, 2),
            })
        rows.sort(key=lambda r: (r['product'].lower(), r['warehouse'].lower()))
        return rows

    def _stock_movement_summary(self, rows):
        total_in = sum(r['total_in'] for r in rows)
        total_out = sum(r['total_out'] for r in rows)
        return {
            'total_in': float_round(total_in, 2),
            'total_out': float_round(total_out, 2),
            'balance': float_round(total_in - total_out, 2),
            'row_count': len(rows),
            'product_count': len({r['product_id'] for r in rows}),
        }

    def _product_balances_by_bucket_at_date(self, as_of_date=None):
        """Return {bucket: {product_id: qty}} for internal stock at a date."""
        today = fields.Date.context_today(self)
        as_of = fields.Date.to_date(as_of_date) if as_of_date else today
        result = {
            'fg': defaultdict(float),
            'raw': defaultdict(float),
            'packaging': defaultdict(float),
            'spare': defaultdict(float),
        }
        warehouses = self._company_warehouses()

        if as_of >= today:
            quants = self.env['stock.quant'].search(self._internal_quant_domain())
            for quant in quants:
                if not quant.quantity:
                    continue
                bucket = self._quant_stock_bucket(quant, warehouses)
                if bucket in result:
                    result[bucket][quant.product_id.id] += quant.quantity
            return result

        balances = defaultdict(float)
        moves = self.env['stock.move'].search([
            ('state', '=', 'done'),
            ('date', '<=', self._dt_end(as_of)),
            *self._company_domain('stock.move'),
            ('product_id', '!=', False),
        ])
        for move in moves:
            qty = move.quantity or 0.0
            if not qty:
                continue
            product = move.product_id
            if move.location_dest_id.usage == 'internal':
                wh = self._location_warehouse(move.location_dest_id, warehouses)
                bucket = self._warehouse_bucket(wh) or self._product_bucket(product)
                if bucket in result:
                    balances[(bucket, product.id)] += qty
            if move.location_id.usage == 'internal':
                wh = self._location_warehouse(move.location_id, warehouses)
                bucket = self._warehouse_bucket(wh) or self._product_bucket(product)
                if bucket in result:
                    balances[(bucket, product.id)] -= qty

        for (bucket, product_id), qty in balances.items():
            if qty:
                result[bucket][product_id] += qty
        return result

    def _stock_values_by_bucket(self, as_of_date=None):
        """Stock value by warehouse bucket at a date (current quants or historical)."""
        today = fields.Date.context_today(self)
        as_of = fields.Date.to_date(as_of_date) if as_of_date else today
        buckets = {'fg': 0.0, 'raw': 0.0, 'packaging': 0.0, 'spare': 0.0}

        if as_of >= today:
            warehouses = self._company_warehouses()
            quants = self.env['stock.quant'].search(self._internal_quant_domain())
            for quant in quants:
                if not quant.quantity:
                    continue
                bucket = self._quant_stock_bucket(quant, warehouses)
                buckets[bucket] += self._quant_value(quant)
            return buckets

        balances = self._product_balances_by_bucket_at_date(as_of)
        product_ids = {
            pid for bucket_map in balances.values() for pid in bucket_map
        }
        products = self.env['product.product'].with_company(self.env.company).browse(
            list(product_ids),
        )
        price_map = {
            p.id: float(p.standard_price or p.list_price or 0.0) for p in products
        }
        for bucket, product_map in balances.items():
            for product_id, qty in product_map.items():
                if qty:
                    buckets[bucket] += abs(qty * price_map.get(product_id, 0.0))
        return buckets

    def _product_reserved_qty_map(self, product_ids):
        """Current reserved qty per product (only meaningful for on-hand quants)."""
        if not product_ids:
            return {}
        reserved = defaultdict(float)
        quants = self.env['stock.quant'].search(
            self._internal_quant_domain() + [('product_id', 'in', list(product_ids))]
        )
        for quant in quants:
            reserved[quant.product_id.id] += quant.reserved_quantity or 0.0
        return reserved

    def _compute_kpis(self, start, end, prev_start, prev_end, range_key='custom'):
        env = self.env
        PurchaseOrder = env['purchase.order']
        MrpProduction = env['mrp.production']
        SaleOrder = env['sale.order']

        def purchase_total(d_start, d_end):
            pos = PurchaseOrder.search([
                ('state', 'in', self._po_states()),
                *self._company_domain('purchase.order'),
                ('date_order', '>=', self._dt_start(d_start)),
                ('date_order', '<=', self._dt_end(d_end)),
            ])
            total = sum(pos.mapped('amount_total'))
            if total:
                return total
            bills = self._posted_vendor_bills(d_start, d_end)
            return sum(
                b.amount_untaxed if b.amount_untaxed else b.amount_total
                for b in bills
            )

        def production_cost(d_start, d_end):
            mos = MrpProduction.search(self._mo_period_domain(d_start, d_end))
            raw_move_ids = self._mo_raw_move_ids(mos.ids)
            return self._stock_move_cost_total(raw_move_ids)

        def sales_total(d_start, d_end):
            invoices = self._posted_customer_invoices(d_start, d_end)
            inv_total = sum(
                inv.amount_untaxed if inv.amount_untaxed else inv.amount_total
                for inv in invoices
            )
            if inv_total:
                return inv_total
            orders = SaleOrder.search([
                ('state', 'in', self._so_states()),
                *self._company_domain('sale.order'),
                ('date_order', '>=', self._dt_start(d_start)),
                ('date_order', '<=', self._dt_end(d_end)),
            ])
            return sum(orders.mapped('amount_total'))

        def stock_values_by_bucket(as_of_date=None):
            return self._stock_values_by_bucket(as_of_date)

        buckets = stock_values_by_bucket(end)
        stock_prev = stock_values_by_bucket(prev_end)
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
            'finished_goods_stock_value': stock_prev['fg'],
            'raw_material_stock_value': stock_prev['raw'],
            'packaging_stock_value': stock_prev['packaging'],
            'spare_part_stock_value': stock_prev['spare'],
        }
        trends = {k: self._trend_pct(cur.get(k), prev.get(k)) for k in cur}

        # Raw numbers for the frontend (ETB formatting done in JS)
        values = {k: float_round(v, precision_digits=2) for k, v in cur.items()}
        return {'values': values, 'trends': trends}

    def _model_available(self, model_name):
        return model_name in self.env

    def _count_records_in_period(self, model_name, date_field, start, end, extra_domain=None):
        """Return record count for a model in the period, or None if model is missing."""
        if not self._model_available(model_name):
            return None
        domain = list(extra_domain or [])
        field = self.env[model_name]._fields.get(date_field)
        if field and field.type == 'datetime':
            domain += [
                (date_field, '>=', self._dt_start(start)),
                (date_field, '<=', self._dt_end(end)),
            ]
        else:
            domain += [
                (date_field, '>=', start),
                (date_field, '<=', end),
            ]
        if 'company_id' in self.env[model_name]._fields:
            domain += self._company_domain(model_name)
        return self.env[model_name].search_count(domain)

    def _compute_workflow_kpis(self, start, end, prev_start, prev_end):
        """Counts for service requests, sales agreements, and purchase agreements."""
        specs = (
            ('service_requests', 'service.request', 'date', _('Service Requests')),
            ('sales_agreements', 'sale.agreement', 'start_date', _('Sales Agreements')),
            ('purchase_agreements', 'supplies.rfp', 'requested_date', _('Purchase Agreements')),
        )
        result = {}
        for key, model, date_field, label in specs:
            current = self._count_records_in_period(model, date_field, start, end)
            if current is None:
                result[key] = {'available': False}
                continue
            previous = self._count_records_in_period(
                model, date_field, prev_start, prev_end,
            ) or 0
            result[key] = {
                'available': True,
                'label': label,
                'model': model,
                'date_field': date_field,
                'count': current,
                'trend': self._trend_pct(current, previous),
            }
        return result

    def _procurement_po_states(self):
        """PO states included in the vendor liability table."""
        states = list(self._po_states())
        selection = dict(self.env['purchase.order']._fields['state'].selection)
        for extra in ('submit', 'to approve'):
            if extra in selection and extra not in states:
                states.append(extra)
        return tuple(states)

    def _compute_procurement(self, start, end):
        PurchaseOrder = self.env['purchase.order']
        dt_start, dt_end = self._dt_start(start), self._dt_end(end)
        orders = PurchaseOrder.search([
            ('state', 'in', self._procurement_po_states()),
            *self._company_domain('purchase.order'),
            ('date_order', '>=', dt_start),
            ('date_order', '<=', dt_end),
        ], order='date_order desc', limit=200)
        rows = []
        for po in orders:
            done_pickings = po.picking_ids.filtered(
                lambda p, ds=dt_start, de=dt_end: (
                    p.state == 'done'
                    and p.date_done
                    and ds <= p.date_done <= de
                )
            )
            grn_move_ids = done_pickings.move_ids_without_package.ids
            grn_qty = self._sum_stock_move_qty(grn_move_ids)
            grn_amount = 0.0
            for line in self._stock_move_lines_data(grn_move_ids):
                unit_price = line['price_unit'] or line['standard_price']
                grn_amount += line['quantity'] * unit_price
            bills = po.invoice_ids.filtered(
                lambda m, ps=start, pe=end: (
                    m.move_type in ('in_invoice', 'in_refund')
                    and m.state == 'posted'
                    and m.invoice_date
                    and ps <= m.invoice_date <= pe
                )
            )
            bill_amount = sum(bills.mapped('amount_total'))
            paid = bill_amount - sum(bills.mapped('amount_residual'))
            remaining = bill_amount - paid if bill_amount else po.amount_total - paid
            rows.append({
                'po_no': po.name,
                'supplier': po.partner_id.display_name,
                'po_qty': sum(po.order_line.mapped('product_qty')),
                'po_amount': self._fmt_money(po.amount_total),
                'grn_qty': grn_qty,
                'grn_amount': self._fmt_money(grn_amount),
                'bill_amount': self._fmt_money(bill_amount),
                'paid_amount': self._fmt_money(paid),
                'remaining': self._fmt_money(remaining),
                'payment_status': self._payment_status(bill_amount, paid),
            })
        if not rows:
            bills = self._posted_vendor_bills(start, end)
            for bill in bills.sorted('invoice_date', reverse=True)[:100]:
                paid = bill.amount_total - bill.amount_residual
                rows.append({
                    'po_no': bill.name,
                    'supplier': bill.partner_id.display_name,
                    'po_qty': '—',
                    'po_amount': self._fmt_money(bill.amount_total),
                    'grn_qty': '—',
                    'grn_amount': self._fmt_money(0),
                    'bill_amount': self._fmt_money(bill.amount_total),
                    'paid_amount': self._fmt_money(paid),
                    'remaining': self._fmt_money(bill.amount_residual),
                    'payment_status': self._payment_status(bill.amount_total, paid),
                })
        return rows

    def _compute_manufacturing(self, start, end):
        MrpProduction = self.env['mrp.production']
        mos = MrpProduction.search(
            self._mo_period_domain(start, end),
            order='date_finished desc, id desc',
            limit=200,
        )

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
            if self._stock_move_has_column('production_id'):
                self.env.cr.execute(
                    """
                    SELECT id FROM stock_move
                    WHERE production_id = %s AND product_id != %s
                    """,
                    (mo.id, mo.product_id.id),
                )
                fin_ids = [r[0] for r in self.env.cr.fetchall()]
            else:
                fin_ids = []
            for line in self._stock_move_lines_data(fin_ids):
                qty = line['quantity']
                byproduct_qty += qty
                byproduct_rows.append({
                    'product': mo.product_id.display_name,
                    'byproduct': line['product_name'],
                    'qty': self._fmt_qty(qty, line['uom_name']),
                    'estimated_value': self._fmt_money(
                        qty * line['standard_price']
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
            raw_ids = []
            if self._stock_move_has_column('raw_material_production_id'):
                self.env.cr.execute(
                    "SELECT id FROM stock_move WHERE raw_material_production_id = %s",
                    (mo.id,),
                )
                raw_ids = [r[0] for r in self.env.cr.fetchall()]
            else:
                raw_ids = []
            actual_map = defaultdict(float)
            for pid, qty in self._stock_move_qty_by_product(raw_ids).items():
                actual_map[pid] += qty

            product_ids = set(planned_map) | set(actual_map)
            for pid in product_ids:
                product = self.env['product.product'].browse(pid)
                p_qty = planned_map.get(pid, 0.0)
                a_qty = actual_map.get(pid, 0.0)
                variance = a_qty - p_qty
                cost_impact = variance * product.standard_price
                sign = '+' if variance >= 0 else ''
                consumption_rows.append({
                    'product': product.display_name,
                    'mo_no': mo.name,
                    'planned': self._fmt_qty(p_qty, product.uom_id.name),
                    'actual': self._fmt_qty(a_qty, product.uom_id.name),
                    'variance': f'{sign}{float_round(variance, 2)} {product.uom_id.name}',
                    'cost_impact': self._fmt_money(cost_impact),
                })

        return efficiency_rows, consumption_rows, byproduct_rows

    def _compute_fg_inventory(self, start, end):
        """FG products: stock summary for the selected period."""
        MrpProduction = self.env['mrp.production']
        fg_balances = self._product_balances_by_bucket_at_date(end)['fg']
        active_product_ids = set(fg_balances.keys())

        for mo in MrpProduction.search(self._mo_period_domain(start, end)):
            active_product_ids.add(mo.product_id.id)

        self.env.cr.execute(
            """
            SELECT DISTINCT sm.product_id
            FROM stock_move sm
            JOIN stock_location sl ON sm.location_dest_id = sl.id
            WHERE sm.state = 'done'
              AND sl.usage = 'customer'
              AND sm.date >= %s
              AND sm.date <= %s
              AND sm.company_id = %s
            """,
            (self._dt_start(start), self._dt_end(end), self.env.company.id),
        )
        active_product_ids.update(row[0] for row in self.env.cr.fetchall())

        rows = []
        for product in self.env['product.product'].browse(list(active_product_ids)):
            ending_qty = fg_balances.get(product.id, 0.0)
            mo_domain = self._mo_period_domain(start, end) + [('product_id', '=', product.id)]
            produced = sum(MrpProduction.search(mo_domain).mapped('qty_produced'))
            sold = self._product_sold_qty_sql(
                product.id, self._dt_start(start), self._dt_end(end),
            )
            if not ending_qty and not produced and not sold:
                continue

            price = float(
                product.with_company(self.env.company).standard_price
                or product.list_price
                or 0.0
            )
            stock_value = abs(ending_qty * price)
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
        return rows[:80]

    def _compute_stock_tables(self, start, end):
        StockMove = self.env['stock.move']
        today = fields.Date.context_today(self)
        warehouses = self._company_warehouses()
        balances_at_end = self._product_balances_by_bucket_at_date(end)

        raw_rows, pack_rows, spare_rows = [], [], []
        consumption_domain = [
            ('state', '=', 'done'),
            ('date', '>=', self._dt_start(start)),
            ('date', '<=', self._dt_end(end)),
        ]
        consumed_moves = StockMove.search(consumption_domain)

        bucket_products = {
            'raw': set(balances_at_end['raw'].keys()),
            'packaging': set(balances_at_end['packaging'].keys()),
            'spare': set(balances_at_end['spare'].keys()),
        }
        consumption_by_bucket_product = {
            'raw': defaultdict(float),
            'packaging': defaultdict(float),
            'spare': defaultdict(float),
        }
        for move in consumed_moves:
            if move.location_dest_id.usage not in ('production', 'customer'):
                continue
            product = move.product_id
            qty = move.quantity or 0.0
            if not qty:
                continue
            if move.location_id.usage == 'internal':
                wh = self._location_warehouse(move.location_id, warehouses)
                bucket = self._warehouse_bucket(wh) or self._product_bucket(product)
            else:
                bucket = self._product_bucket(product)
            if bucket not in bucket_products:
                continue
            bucket_products[bucket].add(product.id)
            consumption_by_bucket_product[bucket][product.id] += qty

        all_product_ids = set().union(*bucket_products.values())
        reserved_map = {}
        if fields.Date.to_date(end) >= today:
            reserved_map = self._product_reserved_qty_map(all_product_ids)

        products = self.env['product.product'].with_company(self.env.company).browse(
            list(all_product_ids),
        )
        price_map = {
            p.id: float(p.standard_price or p.list_price or 0.0) for p in products
        }

        for bucket, rows_target in (
            ('raw', raw_rows),
            ('packaging', pack_rows),
            ('spare', spare_rows),
        ):
            for pid in bucket_products[bucket]:
                product = self.env['product.product'].browse(pid)
                available = balances_at_end[bucket].get(pid, 0.0)
                consumption = consumption_by_bucket_product[bucket].get(pid, 0.0)
                if available <= 0 and consumption <= 0:
                    continue

                reserved = reserved_map.get(pid, 0.0) if available > 0 else 0.0
                free = available - reserved
                value = abs(available * price_map.get(pid, 0.0))
                uom = product.uom_id.name

                if bucket == 'packaging':
                    rows_target.append({
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
                    rows_target.append({
                        'part': product.display_name,
                        'available': self._fmt_qty(available, uom),
                        'status': self._stock_status(free, minimum),
                        'stock_value': self._fmt_money(value),
                        '_sort_value': value,
                    })
                else:
                    rows_target.append({
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
            *self._company_domain('stock.picking'),
            ('date_done', '>=', self._dt_start(start)),
            ('date_done', '<=', self._dt_end(end)),
        ], order='date_done desc', limit=200)

        rows = []
        for picking in pickings:
            sale = picking.sale_id
            customer = picking.partner_id.display_name or (
                sale.partner_id.display_name if sale else ''
            )
            service = ''
            if sale and 'service_request_id' in sale._fields and sale.service_request_id:
                service = sale.service_request_id.display_name
            for line in self._stock_move_lines_data(picking.move_ids_without_package.ids):
                invoiced_qty = line['quantity']
                if sale:
                    sol = sale.order_line.filtered(
                        lambda l, pid=line['product_id']: l.product_id.id == pid
                    )
                    if sol:
                        invoiced_qty = sum(sol.mapped('qty_invoiced'))
                rows.append({
                    'do_no': picking.name,
                    'customer': customer,
                    'product': line['product_name'],
                    'service': service or '—',
                    'delivered_qty': self._fmt_qty(line['quantity'], line['uom_name']),
                    'invoiced_qty': self._fmt_qty(invoiced_qty, line['uom_name']),
                    'delivery_status': 'Delivered',
                })
        return rows

    def _compute_customer_collections(self, start, end):
        invoices = self._posted_customer_invoices(start, end)
        invoices = invoices.sorted('invoice_date', reverse=True)[:200]

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

    def _compute_partner_ledger(self, start, end):
        """Partner ledger lines on receivable/payable accounts for the period."""
        AML = self.env['account.move.line']
        domain = [
            ('parent_state', '=', 'posted'),
            ('date', '>=', start),
            ('date', '<=', end),
            *self._company_domain('account.move.line'),
            ('partner_id', '!=', False),
            ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
        ]
        lines = AML.search(domain, order='partner_id, date, id', limit=1000)
        empty_payload = {
            'lines': [],
            'partners': [],
            'partner_totals': [],
            'grand_total': {
                'partner': 'Grand Total',
                'debit': 0.0,
                'credit': 0.0,
                'balance': 0.0,
                'debit_raw': 0.0,
                'credit_raw': 0.0,
                'balance_raw': 0.0,
            },
        }
        if not lines:
            domain = [
                ('parent_state', '=', 'posted'),
                ('date', '>=', start),
                ('date', '<=', end),
                *self._company_domain('account.move.line'),
                ('partner_id', '!=', False),
                ('account_id.internal_group', 'in', ('receivable', 'payable')),
            ]
            lines = AML.search(domain, order='partner_id, date, id', limit=1000)
        if not lines:
            empty_payload['grand_total'].update({
                'debit': self._fmt_money(0),
                'credit': self._fmt_money(0),
                'balance': self._fmt_money(0),
            })
            return empty_payload
        by_partner = defaultdict(list)
        for line in lines:
            by_partner[line.partner_id.id].append(line)

        partner_options = []
        partner_totals = []
        rows = []
        grand_debit = grand_credit = 0.0

        for partner_id, plines in sorted(
            by_partner.items(), key=lambda item: item[1][0].partner_id.display_name
        ):
            partner = plines[0].partner_id
            partner_options.append({
                'id': partner_id,
                'name': partner.display_name,
            })
            balance = 0.0
            p_debit = p_credit = 0.0
            partner_rows = []
            for line in plines:
                line_debit = line.debit or 0.0
                line_credit = line.credit or 0.0
                balance += line_debit - line_credit
                p_debit += line_debit
                p_credit += line_credit
                account = line.account_id
                account_label = (
                    f'{account.code} {account.name}'.strip()
                    if account.code
                    else account.display_name
                )
                account_type = getattr(account, 'account_type', False)
                if account_type == 'asset_receivable':
                    type_label = 'Receivable'
                elif account_type == 'liability_payable':
                    type_label = 'Payable'
                elif getattr(account, 'internal_group', None) == 'receivable':
                    type_label = 'Receivable'
                else:
                    type_label = 'Payable'
                partner_rows.append({
                    'date': fields.Date.to_string(line.date),
                    'partner_id': partner_id,
                    'partner': partner.display_name,
                    'account': account_label,
                    'account_type': type_label,
                    'move': line.move_id.name or '',
                    'label': (line.name or line.move_id.ref or '')[:120],
                    'debit': self._fmt_money(line_debit),
                    'credit': self._fmt_money(line_credit),
                    'balance': self._fmt_money(balance),
                    'debit_raw': line_debit,
                    'credit_raw': line_credit,
                    'balance_raw': balance,
                    '_sort_date': line.date,
                    '_sort_id': line.id,
                })
            partner_rows.reverse()
            rows.extend(partner_rows)
            partner_totals.append({
                'partner_id': partner_id,
                'partner': partner.display_name,
                'debit': self._fmt_money(p_debit),
                'credit': self._fmt_money(p_credit),
                'balance': self._fmt_money(p_debit - p_credit),
                'debit_raw': p_debit,
                'credit_raw': p_credit,
                'balance_raw': p_debit - p_credit,
            })
            grand_debit += p_debit
            grand_credit += p_credit

        rows.sort(key=lambda r: (r['_sort_date'], r['_sort_id']), reverse=True)
        for row in rows:
            row.pop('_sort_date', None)
            row.pop('_sort_id', None)

        return {
            'lines': rows,
            'partners': partner_options,
            'partner_totals': partner_totals,
            'grand_total': {
                'partner': 'Grand Total',
                'debit': self._fmt_money(grand_debit),
                'credit': self._fmt_money(grand_credit),
                'balance': self._fmt_money(grand_debit - grand_credit),
                'debit_raw': grand_debit,
                'credit_raw': grand_credit,
                'balance_raw': grand_debit - grand_credit,
            },
        }

    def _compute_profitability(self, start, end):
        MrpProduction = self.env['mrp.production']

        revenue_by_product = defaultdict(float)
        invoices = self._posted_customer_invoices(start, end)
        for inv in invoices:
            for line in inv.invoice_line_ids.filtered(
                lambda l: not l.display_type and l.product_id
            ):
                revenue_by_product[line.product_id.id] += line.price_subtotal

        if not revenue_by_product:
            orders = self.env['sale.order'].search([
                ('state', 'in', self._so_states()),
                *self._company_domain('sale.order'),
                ('date_order', '>=', self._dt_start(start)),
                ('date_order', '<=', self._dt_end(end)),
            ])
            for order in orders:
                for line in order.order_line.filtered(lambda l: not l.display_type):
                    revenue_by_product[line.product_id.id] += line.price_subtotal

        cost_by_product = defaultdict(float)
        mos = MrpProduction.search(self._mo_period_domain(start, end))
        for mo in mos:
            raw_ids = []
            if self._stock_move_has_column('raw_material_production_id'):
                self.env.cr.execute(
                    "SELECT id FROM stock_move WHERE raw_material_production_id = %s",
                    (mo.id,),
                )
                raw_ids = [r[0] for r in self.env.cr.fetchall()]
            else:
                raw_ids = []
            cost_by_product[mo.product_id.id] += self._stock_move_cost_total(raw_ids)

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
            if float(c.get('remaining_raw', c.get('remaining', 0)) or 0) > 0
        ][:8]
        if coll_with_balance:
            coll_labels = [c['customer'] for c in coll_with_balance]
            coll_data = [
                float(c.get('remaining_raw', c.get('remaining', 0)) or 0)
                for c in coll_with_balance
            ]
        elif collections:
            total_inv = sum(float(c.get('invoice_amount', 0) or 0) for c in collections)
            total_col = sum(float(c.get('collected_amount', 0) or 0) for c in collections)
            coll_labels = ['Collected', 'Outstanding']
            coll_data = [total_col, max(total_inv - total_col, 0.0)]
        else:
            coll_labels = ['No invoices in period']
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
