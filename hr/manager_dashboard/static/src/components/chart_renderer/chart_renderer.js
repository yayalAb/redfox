/** @odoo-module **/

import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useRef, onMounted, onPatched } = owl;

export class ChartRenderer extends Component {
    static template = "manager_dashboard.ChartRenderer";
    static props = {
        type: String,
        title: { type: String, optional: true },
        y_title: { type: String, optional: true },
        x_title: { type: String, optional: true },
        data: Object,
        chartId: { type: String, optional: true },
        onChartClick: { type: Function, optional: true },
    };

    setup() {
        // Generate unique chart ID if not provided
        this.chartId = this.props.chartId || `chart-${Math.random().toString(36).substr(2, 9)}`;
        this.chartRef = useRef("chart");
        this.chartInstance = null;
        
        // Expose chartId for template
        this.state = { chartId: this.chartId };

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

        // Destroy existing chart instance if it exists
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }

        const ctx = this.chartRef.el.getContext("2d");
        
        // Configure options based on chart type
        const isPieChart = this.props.type === 'pie';
        const options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { 
                    display: !!this.props.title && this.props.title !== '', 
                    text: this.props.title || '' 
                },
                legend: { 
                    display: true,
                    position: isPieChart ? 'right' : 'top',
                    labels: {
                        boxWidth: 12,
                        padding: 8,
                        font: {
                            size: 10
                        }
                    }
                },
            },
        };

        // Add scales only for non-pie charts
        if (!isPieChart) {
            options.scales = {
                y: {
                    beginAtZero: true,
                    title: { 
                        display: !!this.props.y_title && this.props.y_title !== '', 
                        text: this.props.y_title || '' 
                    },
                },
                x: {
                    title: { 
                        display: !!this.props.x_title && this.props.x_title !== '', 
                        text: this.props.x_title || '' 
                    },
                },
            };
        }

        // Add click handler if provided
        if (this.props.onChartClick) {
            options.onClick = (evt, elements) => {
                if (elements.length > 0) {
                    const element = elements[0];
                    const datasetIndex = element.datasetIndex;
                    const index = element.index;
                    const dataset = this.props.data.datasets[datasetIndex];
                    const label = this.props.data.labels[index];
                    const datasetLabel = dataset.label || "";
                    this.props.onChartClick({
                        chartType: this.props.type,
                        label,
                        datasetLabel,
                    });
                }
            };
        }

        this.chartInstance = new Chart(ctx, {
            type: this.props.type,
            data: this.props.data,
            options: options,
        });
    }

    updateChart() {
        if (this.chartInstance && this.props.data) {
            this.chartInstance.data = this.props.data;
            this.chartInstance.update();
        }
    }
}

