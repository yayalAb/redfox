/** @odoo-module **/

import { registry } from "@web/core/registry"
import { DashboardCard } from "./dashboard_card/dashboard_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { useService } from "@web/core/utils/hooks"

const { Component, onWillStart, useState } = owl

export class MainDashboard extends Component {
    setup() {
        this.state = useState({
            campaign_plans: [],
            selected_plan_id: "",
            start_date: "",
            end_date: "",
            available_shop: { value: 0, percentage: 0 },
            ranted_shop: { value: 0, percentage: 0 },
            this_collection: { value: 0, percentage: 0 },
            expiring_contract: { value: 0, percentage: 0 },
            expecting_collection: { value: 0, percentage: 0 },
            expired_contract: { value: 0, percentage: 0 },

            collection_by_month: {
                labels: [],
                datasets: [
                    {
                        label: "",
                        data: [],
                        backgroundColor: [],
                        borderColor: [],
                    },
                ],
            },
            shop_by_state: {
                labels: [],
                datasets: [
                    {
                        label: "",
                        data: [],
                        backgroundColor: [],
                        borderColor: [],
                    },
                ],
            },
        })

        this.orm = useService("orm")
        this.action = useService("action")

        onWillStart(async () => {
            await this.loadCampaignPlans()
            await this.refreshData()
        })

        this.onAvailableShop = () => {
            const domain = this.getDomain()
            domain.push(["state", "=", "available"])
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Available",
                res_model: "sale.order",
                view_mode: "tree",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
            })
        }

        this.onClickRantedShop = () => {
            const domain = this.getDomain()
            domain.push(["state", "=", "rented"])
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Rated Shop",
                res_model: "sale.order",
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
            })
        }

        this.onThisCollection = () => {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Invoice",
                res_model: "account.move",
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: this.getDomain(),
            })
        }

        this.onExpiringContract = () => {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Expiring Contract",
                res_model: "sale.order",
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: this.getDomain(),
            })
        }

        this.onExpectingCollection = () => {
            const domain = this.getDomain()
            domain.push(["state", "=", "in_contract"])
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Expecting",
                res_model: "sale.order",
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
            })
        }

        this.onExpiredContracts = () => {
            const domain = this.getComplaintDomain()
            domain.push(["state", "=", "expired"])
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Expired Contracts",
                res_model: "sale.order",
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
            })
        }

        this.onRegistryComplaint = () => {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Compliant Registry",
                res_model: "sale.order",
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: this.getComplaintDomain(),
            })
        }

        this.onMonthlyCollectionChartClick = ({ chartType, label }) => {
            console.log(`Chart clicked: Type=${chartType}, Label=${label}`)
            const stateMap = {
                Wait: "wait",
                Review: "review",
                Inprogress: "inprogress",
                Done: "done",
            }
            const state = stateMap[label]
            if (state) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    name: `Suggestions - ${label}`,
                    res_model: "sale.order",
                    view_mode: "tree,form",
                    views: [
                        [false, "list"],
                        [false, "form"],
                    ],
                    target: "current",
                    domain: [
                        ["state", "=", state],
                        ...this.getComplaintDomain(),
                    ],
                })
            }
        }

        this.onShopByStateChartClick = ({ chartType, label }) => {
            const stateMap = {
                Draft: "draft",
                "Task Done": "task_done",
                "Lead Done": "lead_done",
                Done: "done",
            }
            const state = stateMap[label]
            if (state) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    name: `Followup - ${label}`,
                    res_model: "sale.order",
                    view_mode: "tree,form",
                    views: [
                        [false, "list"],
                        [false, "form"],
                    ],
                    target: "current",
                    domain: [
                        ["state", "=", state],
                        ...this.getComplaintDomain(),
                    ],
                })
            }
        }
    }

    getDomain() {
        const domain = []
        //        if (this.state.selected_plan_id) {
        //            domain.push(["campaign_id", "=", this.state.selected_plan_id]);
        //        }
        //        if (this.state.start_date) {
        //            domain.push(["create_date", ">=", this.state.start_date]);
        //        }
        //        if (this.state.end_date) {
        //            domain.push(["create_date", "<=", this.state.end_date]);
        //        }
        return domain
    }

    getComplaintDomain() {
        const domain = []
        //        if (this.state.start_date) {
        //            domain.push(["create_date", ">=", this.state.start_date]);
        //        }
        //        if (this.state.end_date) {
        //            domain.push(["create_date", "<=", this.state.end_date]);
        //        }
        return domain
    }

    async loadCampaignPlans() {
        try {
            const plans = await this.orm.searchRead(
                "property.site",
                [],
                ["id", "name"],
                { limit: 100 }
            )
            console.log("Fetched Campaign Plans: ", plans)
            this.state.campaign_plans = plans
        } catch (error) {
            console.error("Error fetching Campaign Plans:", error)
            this.state.campaign_plans = []
        }
    }

    async onPlanChange(ev) {
        const planId = ev.target.value ? parseInt(ev.target.value) : ""
        this.state.selected_plan_id = planId
        console.log("Selected Plan ID:", planId)
        await this.refreshData()
    }

    async onStartDateChange(ev) {
        this.state.start_date = ev.target.value
        console.log("Start Date Changed:", this.state.start_date)
        await this.refreshData()
    }

    async onEndDateChange(ev) {
        this.state.end_date = ev.target.value
        console.log("End Date Changed:", this.state.end_date)
        await this.refreshData()
    }

    async refreshData() {
        await Promise.all([
            this.getAvailableShop(),
            this.getRantedShop(),
            this.getThisCollection(),
            this.getExpiringContract(),
            this.getExpectingCollection(),
            this.getExpiredContract(),

            this.getMonthlyCollectionData(),
            this.getShopByStateData(),
        ])
    }

    async getAvailableShop() {
        try {
            const domain = this.getDomain()
            domain.push(["state", "=", "available"])
            const data = await this.orm.searchRead("sale.order", domain, ["id"])
            const data_all = await this.orm.searchRead("sale.order", [], ["id"])
            this.state.available_shop.value = 48930
            this.state.available_shop.percentage = 80
        } catch (error) {
            this.state.available_shop.value = 0
            this.state.available_shop.percentage = 0
        }
    }

    async getRantedShop() {
        try {
            const domain = this.getDomain()
            domain.push(["state", "=", "rented"])
            const data = await this.orm.searchRead("sale.order", domain, ["id"])
            const data_all = await this.orm.searchRead("sale.order", [], ["id"])
            this.state.ranted_shop.value = Array.isArray(data) ? data.length : 0
            this.state.ranted_shop.percentage = Array.isArray(data)
                ? (data.length / data_all.length) * 100
                : 0
        } catch (error) {
            this.state.ranted_shop.value = 0
            this.state.available_shop.percentage = 0
        }
    }

    async getThisCollection() {
        try {
            const domain = this.getDomain()
            const records = await this.orm.searchRead("account.move", domain, [
                "amount_total_signed",
            ])
            const totalSum = records.reduce(
                (acc, rec) => acc + rec.amount_total_signed,
                0
            )
            const this_totalSum = records.reduce(
                (acc, rec) => acc + rec.amount_total_signed,
                0
            )

            this.state.this_collection.value = totalSum
            this.state.this_collection.percentage =
                (this_totalSum / totalSum) * 100
        } catch (error) {
            this.state.this_collection.value = 0
            this.state.this_collection.percentage = 0
        }
    }

    async getExpiringContract() {
        try {
            const domain = this.getDomain()
            domain.push(["state", "=", "in_contract"])
            const data = await this.orm.searchRead("sale.order", domain, ["id"])
            const all_data = await this.orm.searchRead("sale.order", [], ["id"])
            this.state.expiring_contract.value = Array.isArray(data)
                ? data.length
                : 0
            this.state.expiring_contract.percentage = Array.isArray(all_data)
                ? (data.length / all_data.length) * 100
                : 0
        } catch (error) {
            this.state.expiring_contract.value = 0
            this.state.expiring_contract.percentage = 0
        }
    }

    async getExpectingCollection() {
        try {
            const records = await this.orm.searchRead(
                "sale.order",
                [],
                ["rent_price"]
            )
            const totalSum = records.reduce(
                (acc, rec) => acc + rec.rent_price,
                0
            )
            const this_totalSum = records.reduce(
                (acc, rec) => acc + rec.rent_price,
                0
            )

            this.state.expecting_collection.value = totalSum
            this.state.expecting_collection.percentage =
                (totalSum / this_totalSum) * 100
        } catch (error) {
            this.state.expecting_collection.value = 0
            this.state.expecting_collection.percentage = 0
        }
    }

    async getExpiredContract() {
        try {
            const domain = this.getDomain()
            domain.push(["state", "=", "expired"])
            const data = await this.orm.searchRead("sale.order", domain, ["id"])
            const all_data = await this.orm.searchRead("sale.order", [], ["id"])
            this.state.expired_contract.value = Array.isArray(data)
                ? data.length
                : 0
            this.state.expired_contract.percentage = Array.isArray(all_data)
                ? (data.length / all_data.length) * 100
                : 0
        } catch (error) {
            this.state.expired_contract.value = 0
            this.state.expired_contract.percentage = 0
        }
    }

    async getMonthlyCollectionData() {
        try {
            // Fetch data including the date and amount fields
            const data = await this.orm.searchRead(
                "account.move",
                this.getComplaintDomain(),
                ["date", "amount_total"] // Include date and amount fields
            )

            // Initialize month counts with all months set to 0
            const monthData = {
                jan: 0,
                feb: 0,
                mar: 0,
                apr: 0,
                may: 0,
                jun: 0,
                jul: 0,
                aug: 0,
                sep: 0,
                oct: 0,
                nov: 0,
                dec: 0,
            }

            // Process each record
            data.forEach(record => {
                if (record.date) {
                    const date = new Date(record.date)
                    const month = date.getMonth() // 0-11 (Jan-Dec)
                    const monthKeys = [
                        "jan",
                        "feb",
                        "mar",
                        "apr",
                        "may",
                        "jun",
                        "jul",
                        "aug",
                        "sep",
                        "oct",
                        "nov",
                        "dec",
                    ]
                    const monthKey = monthKeys[month]

                    // Add the amount to the corresponding month
                    if (monthKey in monthData) {
                        monthData[monthKey] += record.amount_total || 0
                    }
                }
            })

            // Prepare the chart data
            this.state.collection_by_month = {
                labels: [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
                datasets: [
                    {
                        label: "Amount by Month",
                        data: [
                            monthData.jan,
                            monthData.feb,
                            monthData.mar,
                            monthData.apr,
                            monthData.may,
                            monthData.jun,
                            monthData.jul,
                            monthData.aug,
                            monthData.sep,
                            monthData.oct,
                            monthData.nov,
                            monthData.dec,
                        ],
                        backgroundColor: [
                            "rgba(255, 99, 132, 1)",
                            "rgba(54, 162, 235, 1)",
                            "rgba(255, 206, 86, 1)",
                            "rgba(75, 192, 192, 1)",
                            "rgba(153, 102, 255, 1)",
                            "rgba(255, 159, 64, 1)",
                            "rgba(255, 99, 132, 1)",
                            "rgba(54, 162, 235, 1)",
                            "rgba(255, 206, 86, 1)",
                            "rgba(75, 192, 192, 1)",
                            "rgba(153, 102, 255, 1)",
                            "rgba(255, 159, 64, 1)",
                        ],
                        borderColor: [
                            "rgba(255, 99, 132, 1)",
                            "rgba(54, 162, 235, 1)",
                            "rgba(255, 206, 86, 1)",
                            "rgba(75, 192, 192, 1)",
                            "rgba(153, 102, 255, 1)",
                            "rgba(255, 159, 64, 1)",
                            "rgba(255, 99, 132, 1)",
                            "rgba(54, 162, 235, 1)",
                            "rgba(255, 206, 86, 1)",
                            "rgba(75, 192, 192, 1)",
                            "rgba(153, 102, 255, 1)",
                            "rgba(255, 159, 64, 1)",
                        ],
                        borderWidth: 1,
                    },
                ],
            }
        } catch (error) {
            console.error("Error fetching  data:", error)
        }
    }

    async getShopByStateData() {
        try {
            const data = await this.orm.searchRead(
                "sale.order",
                this.getComplaintDomain(),
                ["state"]
            )
            const stateCounts = {
                draft: 0,
                available: 0,
                rented: 0,
                sold: 0,
            }
            data.forEach(record => {
                if (record.state in stateCounts) {
                    stateCounts[record.state]++
                }
            })
            this.state.shop_by_state = {
                labels: ["Draft", "Available", "Rented", "Sold"],
                datasets: [
                    {
                        label: "Shop By State",
                        data: [
                            stateCounts.draft,
                            stateCounts.available,
                            stateCounts.rented,
                            stateCounts.sold,
                        ],
                        backgroundColor: [
                            "rgba(153, 102, 255, 1)",
                            "rgba(255, 159, 64, 1)",
                            "rgba(75, 192, 192, 1)",
                            "rgba(54, 162, 235, 1)",
                        ],
                        borderColor: [
                            "rgba(153, 102, 255, 1)",
                            "rgba(255, 159, 64, 1)",
                            "rgba(75, 192, 192, 1)",
                            "rgba(54, 162, 235, 1)",
                        ],
                        borderWidth: 1,
                    },
                ],
            }
        } catch (error) {
            console.error("Error fetching data:", error)
        }
    }
}

MainDashboard.template = "main_dashboard.MainDashboard"
MainDashboard.components = { DashboardCard, ChartRenderer }

registry
    .category("actions")
    .add("main_dashboard.dashboard_main_view", MainDashboard)
