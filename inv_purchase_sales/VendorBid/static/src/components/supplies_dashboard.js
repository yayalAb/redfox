/** @odoo-module */
import { registry } from "@web/core/registry"
const { Component, onWillStart, useRef, onMounted, useState, useEffect } = owl;
import { Layout } from "@web/search/layout";
import { useService } from "@web/core/utils/hooks";
import { StatBar } from "./statbar/statbar";
import { Graph } from "./graph/graph";
import { CompanyCard } from "./company_card/company_card";
import { formatAmount, getDateInterval, groupProducts, getCurrency } from './utils'


export class SuppliesDashboard extends Component {
    setup() {
        this.timeperiods = [
            { tag: 'this_week', label: 'This Week' },
            { tag: 'last_week', label: 'Last Week' },
            { tag: 'last_month', label: 'Last Month' },
            { tag: 'last_year', label: 'Last Year' },
        ];
        this.state = useState({
            suppliers: [],
            selectedSupplierId: "0",
            currency: '',
            selectedPeriod: "0",
            productLineIds: [],
            productLines: [],
            rfpPurchaseChartData: null,
            rfqStatusChartData: null,
            another: 'test',
            rfp: {
                'accepted': 0,
                'submitted': 0,
                'total_amount': 0,
            }
        })
        this.orm = useService('orm');

        onWillStart(async () => {
            await this.getSuppliers();
        });

        useEffect(() => {
            if (this.state.selectedSupplierId !== "0") {
                this.getRequestForPurchases();
            } else {
                this.state.rfp = { accepted: 0, submitted: 0, total_amount: 0 };
                this.state.rfpPurchaseChartData = null;
                this.state.rfqStatusChartData = null;
                this.state.productLines = [];
            }
        }, () => [this.state.selectedSupplierId, this.state.selectedPeriod]);

        useEffect(() => {
            if (this.state.productLineIds.length) {
                this.getProductLines();
            } else {
                this.state.productLines = [];
            }
        }, () => [this.state.productLineIds]);

    }

    async getSuppliers() {
        const suppliers = await this.orm.searchRead('res.partner', [['supplier_rank', '>', 0]], ['name', 'image_1920', 'street']);
        this.state.suppliers = suppliers;        
    }

    setRfpPurchaseData(purchase_orders) {
        if (purchase_orders.length == 0) {
            this.state.rfpPurchaseChartData = null;
            return;
        }
        const data = {
            labels: purchase_orders.map(po => po.name),
            datasets: [
                {
                    label: 'Total Amount',
                    data: purchase_orders.map(po => po.amount_untaxed)
                }
            ]
        }
        this.state.rfpPurchaseChartData = data;
    }

    setRFQStatusData(rfqs) {        
        if (rfqs.length == 0) {
            this.state.rfqStatusChartData = null;
            return;
        }
        const purchase = rfqs.filter(r => r.state === 'purchase').length;
        const draft = rfqs.filter(r => r.state === 'draft').length;
        const cancel = rfqs.filter(r => r.state === 'cancel').length;
        const data = {
            labels: ['Accepted', 'Draft', 'Cancelled'],
            datasets: [
                {
                    label: 'Count',
                    data: [purchase, draft, cancel],
                    backgroundColor: [
                        '#06d6a0',
                        '#468faf',
                        'rgb(255, 99, 132)'
                    ],
                }
            ]
        }
        this.state.rfqStatusChartData = data;
    }

    async getRequestForPurchases() {
        const rfq_domain = [['rfp_id', '!=', false]];
        const purchase_order_domain = [['state', '=', 'purchase']];
        if (this.state.selectedSupplierId !== "0") {
            const supplerIdInt = parseInt(this.state.selectedSupplierId);
            const partner_subdomain = ['partner_id', '=', supplerIdInt];
            rfq_domain.push(partner_subdomain);
            purchase_order_domain.push(partner_subdomain);
        } else {
            return;
        }
        if (this.state.selectedPeriod !== "0") {
            const { start: startDate, end: endDate } = getDateInterval(this.state.selectedPeriod);
            rfq_domain.push(...[['create_date', '>=', startDate], ['create_date', '<=', endDate]]);
            purchase_order_domain.push(['date_approve', '>=', startDate], ['date_approve', '<=', endDate]);
        }

        const purchase_orders = await this.orm.call(
            'purchase.order',
            'get_purchase_order_sudo', 
            [purchase_order_domain, ['name', 'amount_untaxed', 'order_line']]
        );
        const rfqs = await this.orm.call(
            'purchase.order',
            'get_purchase_order_sudo', 
            [rfq_domain, ['state']]
        );
        const submitted = rfqs.length;
        const accepted = purchase_orders.length;
        let total_amount = purchase_orders.reduce((acc, r) => acc + r.amount_untaxed, 0);
        if (!isNaN(total_amount) && total_amount > 0) {
            total_amount = formatAmount(total_amount);
        }
        const productLineIds = purchase_orders.map(r => r.order_line).flat();
        this.state.productLineIds = productLineIds;
        this.state.rfp = { accepted, submitted, total_amount };
        this.setRfpPurchaseData(purchase_orders);
        this.setRFQStatusData(rfqs);
    }

    async getProductLines() {
        const productLines = await this.orm.searchRead(
            'purchase.order.line',
            [['id', 'in', this.state.productLineIds]],
            ['product_id', 'currency_id', 'product_name', 'product_qty', 'price_unit', 'price_subtotal', 'product_image', 'rfp_id']
        );
        this.state.productLines = groupProducts(productLines);
        this.state.currency = getCurrency(productLines);
    }
}

SuppliesDashboard.template = 'supplies.dashboard';
SuppliesDashboard.components = { Layout, Graph, StatBar, CompanyCard };

registry.category("actions").add("supplies.dashboard", SuppliesDashboard);