/** @odoo-module */

const { Component } = owl
export class DashboardCard extends Component {
    static template = "hr_dashboard.DashboardCard"
    static props = {
        name: String,
        text1: String,
        text2: String,
        value: Number,
        percentage: { type: [Number, String], optional: true },
        current_month_count: { type: Number, optional: true },
        iconClass: String,
        bgColor: String,
        uom: String,
        onClick: Function,
        detail_link: String,
    }

    get percentageClass() {
        const percentage = parseFloat(this.props.percentage)
        return percentage >= 0 ? "text-success" : "text-danger"
    }
}
