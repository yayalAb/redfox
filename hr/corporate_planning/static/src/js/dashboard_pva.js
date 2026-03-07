/** @odoo-module */
import { Component, onMounted, useRef, useEffect } from "@odoo/owl";

export class PlanVsActualCharts extends Component {
    setup() {
        this.chartActivityRef = useRef("chart_pva_activity");
        this.chartFinancialRef = useRef("chart_pva_financial");
        this.chartCapexRef = useRef("chart_pva_capex");
        
        // Store instances here
        this.instances = {};

        useEffect(() => {
            this.renderCharts();
        }, () => [this.props.data]);
    }

    renderCharts() {
        if (!this.props.data) return;
        this.draw(this.chartActivityRef, this.props.data.activity, 'Activity');
        this.draw(this.chartFinancialRef, this.props.data.financial, 'Financial');
        this.draw(this.chartCapexRef, this.props.data.capex, 'Capex');
    }

    draw(ref, data, key) {
        if (!ref.el) return;
        
        // 1. Destroy old instance (Fixes "Canvas in use" error here too)
        if (this.instances[key]) {
            this.instances[key].destroy();
        }

        // 2. Logic for Colors
        // Variance: Green if >= 0, Red if < 0
        const varianceColors = data.variance.map(v => v >= 0 ? 'rgb(28, 200, 138, 0.6)' : 'rgb(231, 74, 59, 0.6)');

        // 3. Logic for X-Axis Labels
        // Create [1, 2, 3...] instead of long names
        const numberedLabels = data.labels.map((_, index) => index + 1);
        const realNames = data.labels; // Store real names for Tooltip

        this.instances[key] = new Chart(ref.el, {
            type: 'bar',
            data: {
                labels: numberedLabels, // Use numbers on Axis
                datasets: [
                    {
                        label: 'Actual',
                        data: data.actual,
                        backgroundColor: 'rgb(246, 194, 62, 0.6)', // Yellow (Fixed)
                        stack: 'combined',
                    },
                    {
                        label: 'Variance',
                        data: data.variance,
                        backgroundColor: varianceColors, // Dynamic Array (Green/Red)
                        stack: 'combined',
                    },
                    {
                        label: 'Plan',
                        data: data.plan,
                        backgroundColor: 'rgb(78, 115, 223, 0.6)', // Blue
                        stack: 'combined', 
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                        grid: { display: false },
                        title: { display: true, text: 'Item Sequence No.' }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                },
                plugins: {
                    // 4. Custom Tooltip to show Real Name
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                const index = context[0].dataIndex;
                                return `${index + 1}. ${realNames[index]}`;
                            }
                        }
                    }
                }
            }
        });
    }
}
PlanVsActualCharts.template = "odoo_corporate_planning.PlanVsActualCharts";