/** @odoo-module */

import { Component } from "@odoo/owl";

export class PaginationControls extends Component {
    static template = "mfg_financial_dashboard.PaginationControls";
    static props = {
        page: Number,
        totalPages: Number,
        totalItems: Number,
        pageSize: Number,
        onPageChange: Function,
    };

    get showingFrom() {
        if (!this.props.totalItems) {
            return 0;
        }
        return (this.props.page - 1) * this.props.pageSize + 1;
    }

    get showingTo() {
        return Math.min(this.props.page * this.props.pageSize, this.props.totalItems);
    }

    onPrev() {
        if (this.props.page > 1) {
            this.props.onPageChange(this.props.page - 1);
        }
    }

    onNext() {
        if (this.props.page < this.props.totalPages) {
            this.props.onPageChange(this.props.page + 1);
        }
    }
}
