/** @odoo-module **/

import { Component, onWillStart, useRef, onMounted, onPatched } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class ChartRenderer extends Component {
    static template = "mfg_financial_dashboard.ChartRenderer";

    setup() {
        this.chartRef = useRef("chart");
        this.chartInstance = null;

        onWillStart(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
        });

        onMounted(() => this.renderChart());
        onPatched(() => this.updateChart());
    }

    renderChart() {
        if (!this.chartRef.el || !window.Chart) {
            return;
        }
        if (!this.props.data?.labels?.length || !this.props.data?.datasets?.length) {
            return;
        }
        const ctx = this.chartRef.el.getContext("2d");
        const isPie = ["pie", "doughnut"].includes(this.props.type);
        this.chartInstance = new Chart(ctx, {
            type: this.props.type,
            data: this.props.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: !!this.props.title, text: this.props.title || "" },
                    legend: { display: true },
                },
                scales: isPie
                    ? {}
                    : {
                          y: {
                              beginAtZero: true,
                              title: { display: true, text: this.props.y_title || "" },
                          },
                          x: {
                              title: { display: true, text: this.props.x_title || "" },
                          },
                      },
            },
        });
    }

    updateChart() {
        if (!this.chartInstance || !this.props.data?.labels?.length) {
            return;
        }
        this.chartInstance.data = this.props.data;
        this.chartInstance.update();
    }
}
