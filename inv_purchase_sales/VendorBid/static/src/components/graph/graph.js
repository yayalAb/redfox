/** @odoo-module */
const { Component, onWillStart, useRef, onMounted, useState, useEffect } = owl;
import { loadJS } from "@web/core/assets";

export class Graph extends Component {
    setup() {
        this.chartRef = useRef('chart');
        this.chartInstance = null;

        onWillStart(async () => {
            await loadJS('https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js');
        });

        onMounted(() => {
            this.renderChart();
        });

        useEffect(() => {
            if (this.chartInstance) {
                this.chartInstance.destroy();
            }
            if (typeof this.props === 'object') {
                this.renderChart();
            }
        }, () => [this.props.data]);
    }

    renderChart() {
        this.chartInstance = new Chart(
            this.chartRef.el,
            {
                type: this.props.type,
                data: this.props.data,
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: this.props.title,
                            position: 'bottom',
                        }
                    }
                }
            }
        );
    }
}

Graph.template = 'supplies.graph';