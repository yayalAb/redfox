/** @odoo-module **/

import { Component, onMounted, onWillStart, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { DashboardCard } from "./dashboard_card/dashboard_card";
import { ChartRenderer } from "./chart_renderer/chart_renderer";
import { PaginationControls } from "./pagination_controls/pagination_controls";

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
    "profitability",
];

export class MfgFinancialDashboard extends Component {
    static PAGE_SIZE = 10;

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        const currentYear = new Date().getFullYear();
        this.fiscalYears = [currentYear, currentYear - 1, currentYear - 2];
        const today = new Date();
        const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);

        this.state = useState({
            loading: true,
            start_date: monthStart.toISOString().split("T")[0],
            end_date: today.toISOString().split("T")[0],
            fiscal_year: "",
            year_over_year: false,
            company_name: "",
            subtitle: "",
            period_label: "",
            use_live_data: true,
            kpis: {},
            kpi_trends: {},
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
            profitability: [],
            charts: {
                kpi_overview: { labels: [], datasets: [] },
                collection_outstanding: { labels: [], datasets: [] },
                profitability: { labels: [], datasets: [] },
            },
            pagination: Object.fromEntries(TABLE_SECTIONS.map((k) => [k, 1])),
        });

        this.dashboardRootRef = useRef("dashboardRoot");
        this.dashboardInnerRef = useRef("dashboardInner");

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
        if (s === "critical") {
            return "mfg-dashboard-badge mfg-dashboard-badge--critical";
        }
        if (s === "reorder required") {
            return "mfg-dashboard-badge mfg-dashboard-badge--reorder";
        }
        return "mfg-dashboard-badge mfg-dashboard-badge--open";
    }

    async onStartDateChange(ev) {
        this.state.start_date = ev.target.value;
        await this.refreshData();
    }

    async onEndDateChange(ev) {
        this.state.end_date = ev.target.value;
        await this.refreshData();
    }

    async onYearOverYearChange(ev) {
        this.state.year_over_year = ev.target.checked;
        await this.refreshData();
    }

    async onFiscalYearChange(ev) {
        this.state.fiscal_year = ev.target.value;
        if (this.state.fiscal_year) {
            this.state.start_date = "";
            this.state.end_date = "";
        }
        await this.refreshData();
    }

    kpiTrend(key) {
        return this.state.kpi_trends?.[key] ?? 0;
    }

    paginatedRows(section) {
        const rows = this.state[section] || [];
        const page = this.state.pagination[section] || 1;
        const start = (page - 1) * MfgFinancialDashboard.PAGE_SIZE;
        return rows.slice(start, start + MfgFinancialDashboard.PAGE_SIZE);
    }

    totalPages(section) {
        const total = (this.state[section] || []).length;
        return Math.max(1, Math.ceil(total / MfgFinancialDashboard.PAGE_SIZE));
    }

    totalItems(section) {
        return (this.state[section] || []).length;
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
                date_start: this.state.start_date || false,
                date_end: this.state.end_date || false,
                year_over_year: this.state.year_over_year,
            };
            if (this.state.fiscal_year) {
                kwargs.fiscal_year = this.state.fiscal_year;
            }
            const data = await this.orm.call(
                "mfg.dashboard",
                "get_dashboard_data",
                [],
                kwargs
            );
            Object.assign(this.state, {
                loading: false,
                company_name: data.company_name,
                subtitle: data.subtitle,
                period_label: data.period_label || "",
                use_live_data: true,
                kpis: data.kpis || {},
                kpi_trends: data.kpi_trends || {},
                procurement: data.procurement,
                production_efficiency: data.production_efficiency,
                rm_pm_consumption: data.rm_pm_consumption,
                byproduct_recovery: data.byproduct_recovery,
                fg_inventory: data.fg_inventory,
                raw_material_stock: data.raw_material_stock,
                packaging_stock: data.packaging_stock,
                spare_parts: data.spare_parts,
                delivery_sales: data.delivery_sales,
                customer_collections: data.customer_collections,
                profitability: data.profitability,
                charts: data.charts,
            });
            this.resetPagination();
        } catch (e) {
            console.error("Dashboard load failed:", e);
            this.state.loading = false;
        }
    }

    openPurchaseOrders() {
        this._openAction("purchase.order", "Purchase Orders");
    }

    openManufacturing() {
        this._openAction("mrp.production", "Manufacturing Orders");
    }

    openSales() {
        this._openAction("sale.order", "Sales Orders");
    }

    openStock() {
        this._openAction("stock.quant", "Inventory");
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
}

MfgFinancialDashboard.template = "mfg_financial_dashboard.MainDashboard";
MfgFinancialDashboard.components = { DashboardCard, ChartRenderer, PaginationControls };

registry.category("actions").add("mfg_financial_dashboard.main_view", MfgFinancialDashboard);
