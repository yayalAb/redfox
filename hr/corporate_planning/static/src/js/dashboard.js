/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, useRef, useState } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { PlanVsActualCharts } from "./dashboard_pva";

export class CorporateDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        
        // 1. Reactive State
        this.state = useState({
            filterYear: new Date().getFullYear().toString(),
            filterQuarter: "",
            filterDept: "",
            filterComp: "", // Stores the Company ID
            
            dashboardData: { 
                cards: {
                    doc_name: "Loading...",
                    core_values: 0, pillars: 0, goals: 0, objectives: 0,
                    risk_count: 0, active_projects: 0,
                    avg_performance: 0, budget_utilization: 0,
                    has_budget: false,
                    identity: { vision: '', mission: '', values: [] },
                    
                    strat_rev: 0, strat_exp: 0, strat_profit: 0,
                    aop_revenue: 0, aop_cos: 0, aop_opex: 0, aop_other: 0, aop_capex: 0
                },
                charts: { 
                    pva: null,
                    bsc: { financial: {datasets:[]}, customer: {datasets:[]}, process: {datasets:[]}, learning: {datasets:[]} },
                    finance: { revenue: [], expense: [], profit: [] },
                    years: []
                }, 
                filters: { departments: [], companies: [] }, 
                strategy_usage: [],
                card_links: {}
            }
        });
        
        // Refs
        this.chartFinRef = useRef("chart_fin");
        this.chartCustRef = useRef("chart_cust");
        this.chartProcRef = useRef("chart_proc");
        this.chartLearnRef = useRef("chart_learn");
        this.chartFinanceRef = useRef("chart_main_finance");
        this.chartRevRef = useRef("chart_rev");
        this.chartExpRef = useRef("chart_exp");
        this.chartProfRef = useRef("chart_prof");

        this.mainChartInstances = {};

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.fetchData();
        });

        onMounted(() => {
            this.renderMainCharts();
        });
    }

    async fetchData() {
        // CALL PYTHON with all filters
        const result = await this.orm.call("corporate.planning.dashboard", "get_dashboard_data", [], { 
            filters: {
                year: this.state.filterYear,
                quarter: this.state.filterQuarter,
                department_id: this.state.filterDept,
                company_id: this.state.filterComp // <--- CRITICAL: Send Company ID
            }
        });
        this.state.dashboardData = result;
    }

    async onFilterChange(changedFilter) {
        // LOGIC: If Company changed, we must clear the Department selection
        // because the list of departments in the dropdown will change.
        if (changedFilter === 'company') {
            this.state.filterDept = "";
        }

        await this.fetchData();
        
        // After data returns, re-render charts
        this.renderMainCharts();
        // The HTML (Cards & Dropdowns) updates automatically via Owl Reactivity
    }

    // ... (Keep formatCurrency, onCardClick, renderMainCharts exactly as before) ...
    formatCurrency(value) {
        if (!value) return "0.00";
        return new Intl.NumberFormat('en-ET', { 
            style: 'currency', 
            currency: 'ETB',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0 
        }).format(value);
    }

    onCardClick(type) {
        const links = this.state.dashboardData.card_links;
        const openStrategyView = (viewId) => {
            if (links.strategy_id) {
                this.action.doAction({
                    type: 'ir.actions.act_window',
                    res_model: 'corporate.strategy.document',
                    res_id: links.strategy_id,
                    views: [[viewId || false, 'form']],
                    target: 'current'
                });
            }
        };

        if (type === 'values') openStrategyView(links.view_values_id);
        else if (type === 'pillars') openStrategyView(links.view_pillars_id);
        else if (type === 'goals') openStrategyView(links.view_goals_id);
        else if (type === 'risk') {
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Critical Risks',
                res_model: 'corporate.risk.register',
                domain: [['risk_level', 'in', ['critical', 'significant']]],
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        }
        else if (type === 'project') this.action.doAction("project.open_view_project_all");
        else if (type === 'finance') {
            if (links.budget_ids && links.budget_ids.length > 0) {
                this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: 'Linked Operating Budgets',
                    res_model: 'budget.analytic',
                    domain: [['id', 'in', links.budget_ids]],
                    views: [[false, 'list'], [false, 'form']],
                    target: 'current'
                });
            } else {
                this.action.doAction("corporate_planning.action_financial_analysis");
            }
        }
        else if (type === 'performance') this.action.doAction("corporate_planning.action_bsc_performance_report");
    }

    renderMainCharts() {
        const bsc = this.state.dashboardData.charts.bsc;
        const years = this.state.dashboardData.charts.years;
        const colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'];

        const drawChart = (ref, key, type, data, options) => {
            if (!ref.el) return;
            if (this.mainChartInstances[key]) this.mainChartInstances[key].destroy();
            this.mainChartInstances[key] = new Chart(ref.el, { type, data, options });
        };

        // BSC
        const getBscConfig = (datasets) => {
            if(!datasets) return { labels: [], datasets: [] };
            datasets.forEach((ds, i) => { ds.borderColor = colors[i % colors.length]; ds.fill = false; });
            return { labels: years, datasets: datasets };
        };
        const lineOpts = { responsive: true, maintainAspectRatio: false };
        
        drawChart(this.chartFinRef, 'fin', 'line', getBscConfig(bsc.financial.datasets), lineOpts);
        drawChart(this.chartCustRef, 'cust', 'line', getBscConfig(bsc.customer.datasets), lineOpts);
        drawChart(this.chartProcRef, 'proc', 'line', getBscConfig(bsc.process.datasets), lineOpts);
        drawChart(this.chartLearnRef, 'learn', 'line', getBscConfig(bsc.learning.datasets), lineOpts);

        // Finance
        const fin = this.state.dashboardData.charts.finance;
        const finOpts = { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } };
        
        const getFinConfig = (datasets) => {
            if(!datasets) return { labels: [], datasets: [] };
            datasets.forEach((ds, i) => { ds.backgroundColor = colors[i % colors.length]; });
            return { labels: years, datasets: datasets };
        };

        drawChart(this.chartRevRef, 'rev', 'bar', getFinConfig(fin.revenue), finOpts);
        drawChart(this.chartExpRef, 'exp', 'bar', getFinConfig(fin.expense), finOpts);
        drawChart(this.chartProfRef, 'prof', 'bar', getFinConfig(fin.profit), finOpts);
    }
}
CorporateDashboard.components = { PlanVsActualCharts };
CorporateDashboard.template = "odoo_corporate_planning.Dashboard";
registry.category("actions").add("corporate_dashboard_tag", CorporateDashboard);