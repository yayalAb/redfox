/** @odoo-module */

import { Component } from "@odoo/owl";

export class DashboardCard extends Component {
    static template = "mfg_financial_dashboard.DashboardCard";
    static defaultProps = {
        trendPercent: 0,
        trendCaption: "vs previous period",
        trendTooltip: "",
    };

    static props = {
        name: String,
        displayValue: { type: String, optional: true },
        value: { type: Number, optional: true },
        iconClass: { type: String, optional: true },
        trendPercent: { type: Number, optional: true },
        trendCaption: { type: String, optional: true },
        trendTooltip: { type: String, optional: true },
        onClick: { type: Function, optional: true },
    };

    get trendText() {
        const pct = Number(this.props.trendPercent);
        if (Number.isNaN(pct)) {
            return "0.0%";
        }
        const abs = Math.abs(pct).toFixed(1);
        return `${abs}%`;
    }

    get trendArrow() {
        const pct = Number(this.props.trendPercent) || 0;
        if (pct > 0) {
            return "↑ ";
        }
        if (pct < 0) {
            return "↓ ";
        }
        return "— ";
    }

    onCardClick() {
        if (typeof this.props.onClick === "function") {
            this.props.onClick();
        }
    }
}
