/** @odoo-module **/

import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useRef, onMounted, onPatched } = owl;

export class ChartRenderer extends Component {
    static template = "owl.ChartRenderer";

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
            console.error("Chart.js or canvas not available");
            return;
        }

        // Validate props.data before rendering
        if (!this.props.data || !this.props.data.labels || !this.props.data.datasets || !this.props.data.datasets[0]) {
            console.error("Invalid chart data:", this.props.data);
            return;
        }

        const ctx = this.chartRef.el.getContext("2d");
        this.chartInstance = new Chart(ctx, {
            type: this.props.type,
            data: this.props.data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: this.props.title },
                    legend: { display: true },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: this.props.y_title },
                    },
                    x: {
                        title: { display: true, text: this.props.x_title },
                    },
                },
                onClick: (event, elements) => {
                    if (elements.length > 0 && typeof this.props.onChartClick === "function") {
                        const element = elements[0];
                        const index = element.index;
                        const datasetIndex = element.datasetIndex;
                        const label = this.props.data.labels[index];
                        const datasetLabel = this.props.datasetLabels && this.props.datasetLabels[datasetIndex]
                            ? this.props.datasetLabels[datasetIndex]
                            : this.props.data.datasets[datasetIndex].label;
                        console.log("Chart clicked:", { chartType: this.props.type, label, datasetLabel });
                        this.props.onChartClick({ chartType: this.props.type, label, datasetLabel });
                    } else if (elements.length > 0) {
                        console.warn("onChartClick is not a function");
                    }
                },
            },
        });
    }

    updateChart() {
        if (this.chartInstance) {
            // Validate props.data before updating
            if (!this.props.data || !this.props.data.labels || !this.props.data.datasets || !this.props.data.datasets[0]) {
                console.error("Invalid chart data for update:", this.props.data);
                return;
            }
            this.chartInstance.data = this.props.data;
            this.chartInstance.update();
        }
    }
}