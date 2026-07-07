/** @odoo-module **/

import { Component, onMounted, onWillStart, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { DashboardCard } from "./dashboard_card/dashboard_card";
import { ChartRenderer } from "./chart_renderer/chart_renderer";
import { PaginationControls } from "./pagination_controls/pagination_controls";

/** Format a Date as YYYY-MM-DD in local time (avoids UTC shift from toISOString). */
function formatLocalDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
}

const DATE_RANGE_OPTIONS = [
    { value: "today", label: "Today" },
    { value: "yesterday", label: "Yesterday" },
    { value: "last_7_days", label: "Last 7 Days" },
    { value: "this_week", label: "This Week" },
    { value: "last_week", label: "Last Week" },
    { value: "last_30_days", label: "Last 30 Days" },
    { value: "this_month_mtd", label: "This Month (MTD)" },
    { value: "last_month", label: "Last Month" },
    { value: "this_quarter_qtd", label: "This Quarter (QTD)" },
    { value: "last_quarter", label: "Last Quarter" },
    { value: "this_year_ytd", label: "This Year (YTD)" },
    { value: "last_year", label: "Last Year" },
    { value: "custom", label: "Custom Range" },
];

const TABLE_SECTIONS = [
    "procurement",
    "production_efficiency",
    "rm_pm_consumption",
    "byproduct_recovery",
    "fg_inventory",
    "raw_material_stock",
    "packaging_stock",
    "spare_parts",
    "delivery_sales",
    "customer_collections",
    "partner_ledger",
    "profitability",
    "stock_movement",
];

export class MfgFinancialDashboard extends Component {
    static PAGE_SIZE = 10;
    static DATE_RANGE_OPTIONS = DATE_RANGE_OPTIONS;

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dateRangeOptions = DATE_RANGE_OPTIONS;

        this.state = useState({
            loading: true,
            date_range: "this_year_ytd",
            start_date: "",
            end_date: "",
            comparison_label: "vs same period last year",
            comparison_period_label: "",
            company_name: "",
            subtitle: "",
            period_label: "",
            use_live_data: true,
            kpis: {},
            kpi_trends: {},
            workflow_kpis: {},
            procurement: [],
            production_efficiency: [],
            rm_pm_consumption: [],
            byproduct_recovery: [],
            fg_inventory: [],
            raw_material_stock: [],
            packaging_stock: [],
            spare_parts: [],
            delivery_sales: [],
            customer_collections: [],
            partner_ledger: [],
            partner_ledger_partners: [],
            partner_filter_ids: [],
            profitability: [],
            stock_movements: [],
            stock_movement_summary: {
                total_in: 0,
                total_out: 0,
                balance: 0,
                row_count: 0,
                product_count: 0,
            },
            charts: {
                kpi_overview: { labels: [], datasets: [] },
                collection_outstanding: { labels: [], datasets: [] },
                profitability: { labels: [], datasets: [] },
            },
            pagination: Object.fromEntries(TABLE_SECTIONS.map((k) => [k, 1])),
        });

        this.dashboardRootRef = useRef("dashboardRoot");
        this.dashboardInnerRef = useRef("dashboardInner");

        // Arrow handlers keep `this` when passed as props to DashboardCard.
        this.openPurchaseOrders = () => {
            this._openAction("purchase.order", "Purchase Orders");
        };
        this.openManufacturing = () => {
            this._openAction("mrp.production", "Manufacturing Orders");
        };
        this.openSales = () => {
            this._openAction("sale.order", "Sales Orders");
        };
        this.openStock = () => {
            this._openAction("stock.quant", "Inventory");
        };
        this.openServiceRequests = () => {
            this._openWorkflowRecords("service_requests", "Service Requests");
        };
        this.openSalesAgreements = () => {
            this._openWorkflowRecords("sales_agreements", "Sales Agreements");
        };
        this.openPurchaseAgreements = () => {
            this._openWorkflowRecords("purchase_agreements", "Purchase Agreements");
        };

        onMounted(() => {
            const root = this.dashboardRootRef.el;
            const pane = this.dashboardInnerRef.el;
            if (!root || !pane) {
                return;
            }
            root.style.setProperty("display", "flex", "important");
            root.style.setProperty("flex-direction", "column", "important");
            root.style.setProperty("height", "100%", "important");
            root.style.setProperty("max-height", "100%", "important");
            root.style.setProperty("min-height", "0", "important");
            root.style.setProperty("overflow", "hidden", "important");
            pane.style.setProperty("flex", "1 1 auto", "important");
            pane.style.setProperty("min-height", "0", "important");
            pane.style.setProperty("overflow-y", "auto", "important");
            pane.style.setProperty("overflow-x", "hidden", "important");
        });

        onWillStart(async () => {
            await this.refreshData();
        });
    }

    formatMoney(amount) {
        const n = Number(amount) || 0;
        return new Intl.NumberFormat("en-ET", {
            style: "currency",
            currency: "ETB",
            maximumFractionDigits: 0,
        }).format(n);
    }

    formatCompactMoney(amount) {
        const n = Number(amount) || 0;
        const sign = n < 0 ? "-" : "";
        const abs = Math.abs(n);
        if (abs >= 1_000_000) {
            return `${sign}ETB ${(abs / 1_000_000).toFixed(1)}M`;
        }
        if (abs >= 1_000) {
            return `${sign}ETB ${(abs / 1_000).toFixed(1)}K`;
        }
        if (abs >= 1) {
            return `${sign}ETB ${abs.toFixed(1)}`;
        }
        if (abs > 0) {
            return `${sign}ETB ${abs.toFixed(2)}`;
        }
        return "ETB 0.0";
    }

    statusBadgeClass(status) {
        const s = (status || "").toLowerCase();
        if (s === "paid" || s === "normal") {
            return "mfg-dashboard-badge mfg-dashboard-badge--paid";
        }
        if (s === "partial" || s === "reorder required") {
            return "mfg-dashboard-badge mfg-dashboard-badge--partial";
        }
        if (s === "not billed") {
            return "mfg-dashboard-badge mfg-dashboard-badge--open";
        }
        if (s === "critical") {
            return "mfg-dashboard-badge mfg-dashboard-badge--critical";
        }
        if (s === "reorder required") {
            return "mfg-dashboard-badge mfg-dashboard-badge--reorder";
        }
        return "mfg-dashboard-badge mfg-dashboard-badge--open";
    }

    async onDateRangeChange(ev) {
        this.state.date_range = ev.target.value;
        if (this.state.date_range !== "custom") {
            await this.refreshData();
        }
    }

    async onStartDateChange(ev) {
        this.state.start_date = ev.target.value;
        this.state.date_range = "custom";
        await this.refreshData();
    }

    async onEndDateChange(ev) {
        this.state.end_date = ev.target.value;
        this.state.date_range = "custom";
        await this.refreshData();
    }

    comparisonCaption() {
        return this.state.comparison_label || "vs previous period";
    }

    trendTooltip() {
        const period = this.state.comparison_period_label;
        if (period) {
            return `Percentage change vs comparison period (${period})`;
        }
        return "Percentage change vs the equivalent prior period";
    }

    workflowKpi(key) {
        return this.state.workflow_kpis?.[key] || { available: false };
    }

    workflowCount(key) {
        const kpi = this.workflowKpi(key);
        return kpi.available ? String(kpi.count ?? 0) : "—";
    }

    workflowTrend(key) {
        const kpi = this.workflowKpi(key);
        return kpi.available ? (kpi.trend ?? 0) : 0;
    }

    kpiTrend(key) {
        return this.state.kpi_trends?.[key] ?? 0;
    }

    filteredPartnerLedgerLines() {
        const lines = this.state.partner_ledger || [];
        const ids = this.state.partner_filter_ids || [];
        if (!ids.length) {
            return lines;
        }
        const idSet = new Set(ids.map((id) => Number(id)));
        return lines.filter((row) => idSet.has(Number(row.partner_id)));
    }

    filteredPartnerLedgerPartnerTotals() {
        const ids = this.state.partner_filter_ids || [];
        const totals = this.state.partner_ledger_partner_totals || [];
        if (!ids.length) {
            return totals;
        }
        const idSet = new Set(ids.map((id) => Number(id)));
        return totals.filter((row) => idSet.has(Number(row.partner_id)));
    }

    filteredPartnerLedgerGrandTotal() {
        const totals = this.filteredPartnerLedgerPartnerTotals();
        const grand = totals.reduce(
            (acc, row) => ({
                partner: "Grand Total",
                debit_raw: acc.debit_raw + (Number(row.debit_raw) || 0),
                credit_raw: acc.credit_raw + (Number(row.credit_raw) || 0),
                balance_raw: acc.balance_raw + (Number(row.balance_raw) || 0),
            }),
            { partner: "Grand Total", debit_raw: 0, credit_raw: 0, balance_raw: 0 }
        );
        return grand;
    }

    partnerLedgerDisplayRows() {
        const lines = this.filteredPartnerLedgerLines();
        const byPartner = new Map();
        for (const line of lines) {
            const pid = Number(line.partner_id);
            if (!byPartner.has(pid)) {
                byPartner.set(pid, []);
            }
            byPartner.get(pid).push(line);
        }
        const totalsById = new Map(
            this.filteredPartnerLedgerPartnerTotals().map((t) => [Number(t.partner_id), t])
        );
        const display = [];
        for (const pt of this.filteredPartnerLedgerPartnerTotals()) {
            const pid = Number(pt.partner_id);
            const partnerLines = [...(byPartner.get(pid) || [])].sort((a, b) =>
                (b.date || "").localeCompare(a.date || "")
            );
            if (!partnerLines.length) {
                continue;
            }
            for (const line of partnerLines) {
                display.push({ row_type: "line", ...line });
            }
            display.push({
                row_type: "partner_total",
                partner_id: pid,
                partner: pt.partner,
                debit_raw: pt.debit_raw,
                credit_raw: pt.credit_raw,
                balance_raw: pt.balance_raw,
            });
        }
        for (const [pid, partnerLines] of byPartner) {
            if (totalsById.has(pid)) {
                continue;
            }
            for (const line of partnerLines) {
                display.push({ row_type: "line", ...line });
            }
        }
        const grand = this.filteredPartnerLedgerGrandTotal();
        if (display.length) {
            display.push({
                row_type: "grand_total",
                partner: grand.partner,
                debit_raw: grand.debit_raw,
                credit_raw: grand.credit_raw,
                balance_raw: grand.balance_raw,
            });
        }
        return display;
    }

    partnerLedgerRowKey(row, index) {
        if (row.row_type === "partner_total") {
            return `pt_${row.partner_id}`;
        }
        if (row.row_type === "grand_total") {
            return "grand_total";
        }
        return `line_${row.partner_id}_${index}_${row.move || ""}_${row.date || ""}`;
    }

    tableRows(section) {
        if (section === "partner_ledger") {
            return this.partnerLedgerDisplayRows();
        }
        if (section === "stock_movement") {
            return this.state.stock_movements || [];
        }
        return this.state[section] || [];
    }

    formatQty(qty) {
        return (Number(qty) || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    balanceClass(balance) {
        const value = Number(balance) || 0;
        if (value > 0) {
            return "mfg-dashboard-qty--positive";
        }
        if (value < 0) {
            return "mfg-dashboard-qty--negative";
        }
        return "";
    }

    async openStockMovementDetail(row) {
        const action = await this.orm.call(
            "mfg.dashboard",
            "open_stock_movement_detail",
            [],
            {
                product_id: row.product_id,
                warehouse_id: row.warehouse_id,
                date_start: this.state.start_date,
                date_end: this.state.end_date,
            }
        );
        if (action) {
            await this.action.doAction(action);
        }
    }

    paginatedRows(section) {
        const rows = this.tableRows(section);
        const page = this.state.pagination[section] || 1;
        const start = (page - 1) * MfgFinancialDashboard.PAGE_SIZE;
        return rows.slice(start, start + MfgFinancialDashboard.PAGE_SIZE);
    }

    totalPages(section) {
        const total = this.tableRows(section).length;
        return Math.max(1, Math.ceil(total / MfgFinancialDashboard.PAGE_SIZE));
    }

    totalItems(section) {
        return this.tableRows(section).length;
    }

    partnerFilterDropdownValue() {
        const ids = this.state.partner_filter_ids || [];
        return ids.length ? String(ids[0]) : "";
    }

    onPartnerFilterSelect(ev) {
        const val = ev.target.value;
        this.state.partner_filter_ids = val ? [Number(val)] : [];
        this.state.pagination.partner_ledger = 1;
    }

    currentPage(section) {
        return this.state.pagination[section] || 1;
    }

    onTablePageChange(section, page) {
        const p = Math.max(1, Math.min(page, this.totalPages(section)));
        this.state.pagination[section] = p;
    }

    resetPagination() {
        for (const key of TABLE_SECTIONS) {
            this.state.pagination[key] = 1;
        }
    }

    async refreshData() {
        this.state.loading = true;
        try {
            const kwargs = {
                date_range: this.state.date_range || "this_year_ytd",
            };
            if (this.state.date_range === "custom") {
                kwargs.date_start = this.state.start_date || false;
                kwargs.date_end = this.state.end_date || false;
            }
            const data = await this.orm.call(
                "mfg.dashboard",
                "get_dashboard_data",
                [],
                kwargs
            );
            Object.assign(this.state, {
                loading: false,
                date_range: data.date_range || this.state.date_range,
                start_date: data.date_start || this.state.start_date,
                end_date: data.date_end || this.state.end_date,
                comparison_label: data.comparison_label || this.state.comparison_label,
                comparison_period_label: data.comparison_period_label || "",
                company_name: data.company_name,
                subtitle: data.subtitle,
                period_label: data.period_label || "",
                use_live_data: true,
                kpis: data.kpis || {},
                kpi_trends: data.kpi_trends || {},
                workflow_kpis: data.workflow_kpis || {},
                procurement: data.procurement || [],
                production_efficiency: data.production_efficiency || [],
                rm_pm_consumption: data.rm_pm_consumption || [],
                byproduct_recovery: data.byproduct_recovery || [],
                fg_inventory: data.fg_inventory || [],
                raw_material_stock: data.raw_material_stock || [],
                packaging_stock: data.packaging_stock || [],
                spare_parts: data.spare_parts || [],
                delivery_sales: data.delivery_sales || [],
                customer_collections: data.customer_collections || [],
                partner_ledger: data.partner_ledger || [],
                partner_ledger_partners: data.partner_ledger_partners || [],
                partner_ledger_partner_totals: data.partner_ledger_partner_totals || [],
                partner_ledger_grand_total: data.partner_ledger_grand_total || null,
                partner_filter_ids: [],
                profitability: data.profitability || [],
                stock_movements: data.stock_movements || [],
                stock_movement_summary: data.stock_movement_summary || {
                    total_in: 0,
                    total_out: 0,
                    balance: 0,
                    row_count: 0,
                    product_count: 0,
                },
                charts: data.charts || this.state.charts,
            });
            this.resetPagination();
        } catch (e) {
            console.error("Dashboard load failed:", e);
            this.state.loading = false;
            this.notification.add(
                _t("Could not load dashboard data. Check server logs or your access rights."),
                { type: "danger" }
            );
        }
    }

    _openAction(model, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    _openWorkflowRecords(key, name) {
        const kpi = this.workflowKpi(key);
        if (!kpi.available || !kpi.model) {
            return;
        }
        const domain = [];
        const start = this.state.start_date;
        const end = this.state.end_date;
        if (start && end && kpi.date_field) {
            const isDatetime = kpi.date_field === "requested_date";
            if (isDatetime) {
                domain.push([kpi.date_field, ">=", `${start} 00:00:00`]);
                domain.push([kpi.date_field, "<=", `${end} 23:59:59`]);
            } else {
                domain.push([kpi.date_field, ">=", start]);
                domain.push([kpi.date_field, "<=", end]);
            }
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: kpi.model,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain,
        });
    }
}

MfgFinancialDashboard.template = "mfg_financial_dashboard.MainDashboard";
MfgFinancialDashboard.components = { DashboardCard, ChartRenderer, PaginationControls };

registry.category("actions").add("mfg_financial_dashboard.main_view", MfgFinancialDashboard);
