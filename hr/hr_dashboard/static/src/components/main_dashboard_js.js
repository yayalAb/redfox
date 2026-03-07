/** @odoo-module **/

import { registry } from "@web/core/registry"
import { DashboardCard } from "./dashboard_card/dashboard_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { useService } from "@web/core/utils/hooks"

const { Component, onWillStart, useState } = owl

export class MainDashboard extends Component {
    setup() {
        this.state = useState({
            start_date: "",
            end_date: "",
            exparin_new_contract: { value: 0, uom: "", current_month_count: 0 },
            leave_request: { value: 0, percentage: 0, uom: "Days" },
            hr_employee: { value: 0, uom: "Days" },
            hr_resignation: { value: 0, percentage: 0, uom: "Days" },
            appraisals: { value: 0, percentage: 0, uom: "Days" },
            recruitment: { value: 0, percentage: 0, uom: "Days" },
            expired_contract: { value: 0, percentage: 0, uom: "Days" },
            employee_inventory: {
                labels: [],
                datasets: [
                    {
                        label: "Total Employees",
                        data: [],
                        backgroundColor: "rgba(75, 192, 192, 0.6)",
                        borderColor: "rgba(75, 192, 192, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Male Employees",
                        data: [],
                        backgroundColor: "rgba(54, 162, 235, 0.6)",
                        borderColor: "rgba(54, 162, 235, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Female Employees",
                        data: [],
                        backgroundColor: "rgba(255, 99, 132, 0.6)",
                        borderColor: "rgba(255, 99, 132, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Additions",
                        data: [],
                        backgroundColor: "rgba(255, 206, 86, 0.6)",
                        borderColor: "rgba(255, 206, 86, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Terminations",
                        data: [],
                        backgroundColor: "rgba(255, 159, 64, 0.6)",
                        borderColor: "rgba(255, 159, 64, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Permanent",
                        data: [],
                        backgroundColor: "rgba(153, 102, 255, 0.6)",
                        borderColor: "rgba(153, 102, 255, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Contract",
                        data: [],
                        backgroundColor: "rgba(92, 255, 71, 0.6)",
                        borderColor: "rgb(62, 226, 29)",
                        borderWidth: 1,
                    },
                    {
                        label: "Part Time",
                        data: [],
                        backgroundColor: "rgba(201, 203, 207, 0.6)",
                        borderColor: "rgba(201, 203, 207, 1)",
                        borderWidth: 1,
                    },
                ],
            },
            payroll_by_month: {
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
            appraisal_by_department: {
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
            employee_by_department: {
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
            await this.refreshData()
        })

        this.onContractClick = () => {
            const today = new Date()
            const limitDate = new Date()
            limitDate.setDate(today.getDate() + 30)
            const formattedLimitDate = limitDate.toISOString().split("T")[0]

            const domain = [
                "|",
                ["state", "in", ["draft"]],
                ["date_end", "<=", formattedLimitDate],
            ]

            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Contracts",
                res_model: "hr.contract",
                view_mode: "list",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
                context: { search_default_filter: 0 },
            })
        }

        this.onLeaveRequestClick = () => {
            const domain = this.getDomain()
            domain.push(["state", "in", ["confirm", "validate1"]])
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Rated Shop",
                res_model: "hr.leave",
                view_mode: "list,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
            })
        }

        this.onAappraisal = () => {
            const today = new Date()
            const limitDate = new Date()
            limitDate.setDate(today.getDate() - 30)
            const formattedLimitDate = limitDate.toISOString().split("T")[0]

            const domain = [["create_date", ">=", formattedLimitDate]]
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Invoice",
                res_model: "hr.appraisal",
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
            })
        }

        this.onResignationClick = () => {
            const today = new Date()
            const limitDate = new Date()
            limitDate.setDate(today.getDate() - 30)
            const formattedLimitDate = limitDate.toISOString().split("T")[0]

            const domain = [["create_date", ">=", formattedLimitDate]]
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Resignation",
                res_model: "hr.resignation",
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
            })
        }

        this.onRecruitment = () => {
            const today = new Date()
            const limitDate = new Date()
            limitDate.setDate(today.getDate() - 30)
            const formattedLimitDate = limitDate.toISOString().split("T")[0]

            const domain = [
                ["create_date", ">=", formattedLimitDate],
                ["state", "in", ["open"]],
            ]
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Contracts",
                res_model: "hr.contract",
                view_mode: "list,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
            })
        }

        this.onEmployee = () => {
            const today = new Date()
            const limitDate = new Date()
            limitDate.setDate(today.getDate() - 30)
            const formattedLimitDate = limitDate.toISOString().split("T")[0]

            const domain = [["create_date", ">=", formattedLimitDate]]
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Employee",
                res_model: "hr.employee",
                view_mode: "list,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
            })
        }

        this.onEmployeeInventoryChartClick = ({
            chartType,
            label,
            datasetLabel,
        }) => {
            console.log("Chart clicked:", { chartType, label, datasetLabel })

            // Map month labels to indices
            const monthMap = {
                Jan: 0,
                Feb: 1,
                Mar: 2,
                Apr: 3,
                May: 4,
                Jun: 5,
                Jul: 6,
                Aug: 7,
                Sep: 8,
                Oct: 9,
                Nov: 10,
                Dec: 11,
            }
            const [monthLabel, year] = label.split(" ")
            const monthIndex = monthMap[monthLabel]
            if (monthIndex === undefined || !year) {
                console.error("Invalid month or year:", { monthLabel, year })
                return
            }

            // Calculate full month range explicitly
            const yearNum = parseInt(year)
            const clickedMonthStart = new Date(Date.UTC(yearNum, monthIndex, 1))
            const clickedMonthEnd = new Date(
                Date.UTC(yearNum, monthIndex + 1, 0)
            )

            // Format dates as YYYY-MM-DD
            const formattedStartDate = `${yearNum}-${String(
                monthIndex + 1
            ).padStart(2, "0")}-01`
            const formattedEndDate = `${yearNum}-${String(
                monthIndex + 1
            ).padStart(2, "0")}-${clickedMonthEnd
                .getUTCDate()
                .toString()
                .padStart(2, "0")}`
            console.log("Clicked month range:", {
                clickedMonthStart,
                clickedMonthEnd,
            })
            console.log("Formatted domain dates:", {
                formattedStartDate,
                formattedEndDate,
            })

            // Validate dates
            if (new Date(formattedStartDate) > new Date(formattedEndDate)) {
                console.error("Invalid date range:", {
                    formattedStartDate,
                    formattedEndDate,
                })
                return
            }

            // Base domain from getDomain
            let domain = [...this.getDomain()]
            let res_model = "hr.employee"
            let name = `Employee Inventory - ${label} - ${datasetLabel}`

            switch (datasetLabel) {
                case "Total Employees":
                    domain.push(
                        // ["create_date", ">=", formattedStartDate],
                        ["create_date", "<=", formattedEndDate],
                        ["active", "in", [true, false]]
                    )
                    break
                case "Male Employees":
                    domain.push(
                        // ["create_date", ">=", formattedStartDate],
                        ["create_date", "<=", formattedEndDate],
                        ["gender", "=", "male"],
                        ["active", "in", [true, false]]
                    )
                    break
                case "Female Employees":
                    domain.push(
                        // ["create_date", ">=", formattedStartDate],
                        ["create_date", "<=", formattedEndDate],
                        ["gender", "=", "female"],
                        ["active", "in", [true, false]]
                    )
                    break
                case "Additions":
                    res_model = "hr.contract"
                    domain.push(
                        // ["date_start", ">=", formattedStartDate],
                        ["date_start", "<=", formattedEndDate],
                        ["active", "in", [true, false]]
                        // ["state", "in", ["draft", "open"]]
                    )
                    name = `Contract Additions - ${label}`
                    break
                case "Terminations":
                    res_model = "hr.contract"
                    domain.push(
                        // ["date_end", ">=", formattedStartDate],
                        ["date_end", "<=", formattedEndDate],
                        ["state", "=", "close"],
                        ["active", "in", [true, false]]
                    )
                    name = `Terminations - ${label}`
                    break
                case "Permanent":
                    res_model = "hr.contract"
                    domain.push(
                        // ["date_start", ">=", formattedStartDate],
                        ["date_start", "<=", formattedEndDate],
                        ["active", "in", ["True", "False"]],
                        ["active", "in", [true, false]],

                        // ["state", "in", ["draft", "open"]],
                        ["contract_type_id.name", "ilike", "%Permanent%"]
                    )
                    name = `Permanent Contracts - ${label}`
                    break
                case "Contract":
                    res_model = "hr.contract"
                    domain.push(
                        // ["date_start", ">=", formattedStartDate],
                        ["date_start", "<=", formattedEndDate],
                        ["active", "in", [true, false]],

                        // ["state", "in", ["draft", "open"]],
                        ["contract_type_id.name", "ilike", "%Contractual%"]
                    )
                    name = `Contractual Contracts - ${label}`
                    break
                case "Part Time":
                    res_model = "hr.contract"
                    domain.push(
                        // ["date_start", ">=", formattedStartDate],
                        ["date_start", "<=", formattedEndDate],
                        ["active", "in", [true, false]],

                        // ["state", "in", ["draft", "open"]],
                        ["contract_type_id.name", "ilike", "%Part%Time%"]
                    )
                    name = `Part Time Contracts - ${label}`
                    break
                default:
                    console.error("Unknown datasetLabel:", datasetLabel)
                    return
            }

            console.log("Executing doAction:", { res_model, domain, name })
            this.action.doAction({
                type: "ir.actions.act_window",
                name: name,
                res_model: res_model,
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: domain,
                context: {
                    search_default_filter: 0,
                    default_date_filter: formattedStartDate,
                },
            })
        }

        this.onMonthlyPayrollChartClick = ({ chartType, label }) => {
            const monthMap = {
                Jan: 0,
                Feb: 1,
                Mar: 2,
                Apr: 3,
                May: 4,
                Jun: 5,
                Jul: 6,
                Aug: 7,
                Sep: 8,
                Oct: 9,
                Nov: 10,
                Dec: 11,
            }
            console.log("Month label:", label)
            const monthIndex = monthMap[label]
            console.log("Month Index:", monthIndex)
            if (monthIndex === undefined) return

            const currentYear = new Date().getFullYear()
            const startDate = new Date(currentYear, monthIndex, 1)
            const endDate = new Date(currentYear, monthIndex + 1, 0)

            const formattedStartDate = startDate.toISOString().split("T")[0]
            const formattedEndDate = endDate.toISOString().split("T")[0]

            this.action.doAction({
                type: "ir.actions.act_window",
                name: `Payslips - ${label}`,
                res_model: "hr.payslip",
                view_mode: "tree,form",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
                target: "current",
                domain: [
                    ["create_date", ">=", formattedStartDate],
                    ["create_date", "<=", formattedEndDate],
                ],
            })
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
        return domain
    }

    getComplaintDomain() {
        const domain = []
        return domain
    }

    async onStartDateChange(ev) {
        this.state.start_date = ev.target.value
        await this.refreshData()
    }

    async onEndDateChange(ev) {
        this.state.end_date = ev.target.value
        await this.refreshData()
    }

    async refreshData() {
        await Promise.all([
            this.getExpiringNewContract(),
            this.getLeaveRequest(),
            this.getEmployee(),
            this.getResignation(),
            this.getAppraisal(),
            this.getRecruitment(),
            this.getEmployeeInventoryData(),
            this.getMonthlyPayrollData(),
            this.getEmployeeByDepartmentData(),
            this.getAppraisalByDepartmentData(),
        ])
    }

    async getEmployeeInventoryData() {
        console.log("Entering getEmployeeInventoryData", {
            start_date: this.state.start_date,
            end_date: this.state.end_date,
            domain: this.getDomain(),
        })
        try {
            const domain = this.getDomain()
            console.log("Domain created:", domain)
            const monthLabels = [
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
            ]
            console.log("Month labels defined:", monthLabels)

            let startDate = this.state.start_date
                ? new Date(this.state.start_date)
                : new Date(new Date().getFullYear(), 0, 1)
            let endDate = this.state.end_date
                ? new Date(this.state.end_date)
                : new Date()
            console.log(
                "Parsed startDate:",
                startDate,
                "Input:",
                this.state.start_date
            )
            console.log(
                "Parsed endDate:",
                endDate,
                "Input:",
                this.state.end_date
            )
            if (isNaN(startDate)) {
                console.warn(
                    "Invalid start date, defaulting to start of current year"
                )
                startDate = new Date(new Date().getFullYear(), 0, 1)
                console.log("Defaulted startDate:", startDate)
            }
            if (isNaN(endDate)) {
                console.warn("Invalid end date, defaulting to today")
                endDate = new Date()
                console.log("Defaulted endDate:", endDate)
            }

            startDate = new Date(
                startDate.getFullYear(),
                startDate.getMonth(),
                1
            )
            endDate = new Date(endDate.getFullYear(), endDate.getMonth() + 1, 0)
            console.log("Aligned startDate to first of month:", startDate)
            console.log("Aligned endDate to last of month:", endDate)

            const monthData = {}
            const filteredLabels = []
            let currentDate = new Date(
                startDate.getFullYear(),
                startDate.getMonth(),
                1
            )
            console.log(
                "Starting month iteration with currentDate:",
                currentDate
            )
            const endMonth = new Date(
                endDate.getFullYear(),
                endDate.getMonth() + 1,
                0
            )
            console.log("End month for iteration:", endMonth)

            while (currentDate <= endMonth) {
                const monthKey = `${
                    monthLabels[currentDate.getMonth()]
                } ${currentDate.getFullYear()}`
                console.log("Generating monthKey:", monthKey)
                filteredLabels.push(monthKey)
                monthData[monthKey] = {
                    total: 0,
                    male: 0,
                    female: 0,
                    additions: 0,
                    terminations: 0,
                    permanent: 0,
                    contract: 0,
                    part_time: 0,
                }
                console.log(
                    "Initialized monthData for",
                    monthKey,
                    ":",
                    monthData[monthKey]
                )
                currentDate.setMonth(currentDate.getMonth() + 1)
                console.log("Incremented currentDate to:", currentDate)
            }
            console.log("Generated filteredLabels:", filteredLabels)

            for (const monthKey of filteredLabels) {
                const [monthLabel, year] = monthKey.split(" ")
                const monthIndex = monthLabels.indexOf(monthLabel)
                const monthEnd = new Date(parseInt(year), monthIndex + 1, 0)
                const formattedMonthEnd = monthEnd.toISOString().split("T")[0]
                console.log(`Fetching data for ${monthKey}:`, {
                    formattedMonthEnd,
                })

                try {
                    const employeeDomain = [
                        ["create_date", "<=", formattedMonthEnd],
                        ["active", "in", [true, false]],
                    ]
                    console.log(
                        "Fetching hr.employee data with domain:",
                        employeeDomain,
                        "fields:",
                        ["create_date", "gender"]
                    )
                    const employeeData = await this.orm.searchRead(
                        "hr.employee",
                        employeeDomain,
                        ["create_date", "gender"],
                        { context: { active_test: false } }
                    )
                    console.log(
                        `Received hr.employee data for ${monthKey}:`,
                        employeeData
                    )
                    employeeData.forEach(record => {
                        console.log(
                            `Processing employee record for ${monthKey}:`,
                            record
                        )
                        monthData[monthKey].total += 1
                        console.log(
                            `Incremented total for ${monthKey} to`,
                            monthData[monthKey].total
                        )
                        if (record.gender === "male") {
                            monthData[monthKey].male += 1
                            console.log(
                                `Incremented male for ${monthKey} to`,
                                monthData[monthKey].male
                            )
                        } else if (record.gender === "female") {
                            monthData[monthKey].female += 1
                            console.log(
                                `Incremented female for ${monthKey} to`,
                                monthData[monthKey].female
                            )
                        }
                    })
                } catch (error) {
                    console.error(
                        `Error fetching hr.employee data for ${monthKey}:`,
                        error
                    )
                }

                try {
                    const contractDomain = [
                        ...domain,
                        ["state", "in", ["open", "close", "draft"]],
                        ["date_start", "<=", formattedMonthEnd],
                        ["active", "in", [true, false]],
                    ]
                    const contractFields = [
                        "date_start",
                        "date_end",
                        "state",
                        "contract_type_id",
                    ]
                    console.log(
                        `Fetching hr.contract data for ${monthKey} with domain:`,
                        contractDomain,
                        "fields:",
                        contractFields
                    )
                    const contractData = await this.orm.searchRead(
                        "hr.contract",
                        contractDomain,
                        contractFields,
                        { context: { active_test: false } }
                    )
                    console.log(
                        `Received hr.contract data for ${monthKey}:`,
                        contractData
                    )
                    contractData.forEach(record => {
                        console.log(
                            `Processing contract record for ${monthKey}:`,
                            record
                        )
                        const contractType =
                            record.contract_type_id &&
                            record.contract_type_id.length === 2
                                ? record.contract_type_id[1]
                                : ""
                        console.log(
                            `Determined contractType for ${monthKey}:`,
                            contractType
                        )
                        if (record.date_start) {
                            const startDateRecord = new Date(record.date_start)
                            console.log(
                                `Parsed contract date_start for ${monthKey}:`,
                                startDateRecord
                            )
                            if (startDateRecord <= monthEnd) {
                                monthData[monthKey].additions += 1
                                console.log(
                                    `Incremented additions for ${monthKey} to`,
                                    monthData[monthKey].additions
                                )
                                if (
                                    contractType &&
                                    contractType
                                        .toLowerCase()
                                        .includes("permanent")
                                ) {
                                    monthData[monthKey].permanent += 1
                                    console.log(
                                        `Incremented permanent for ${monthKey} to`,
                                        monthData[monthKey].permanent
                                    )
                                } else if (
                                    contractType &&
                                    contractType
                                        .toLowerCase()
                                        .includes("contractual")
                                ) {
                                    monthData[monthKey].contract += 1
                                    console.log(
                                        `Incremented contract for ${monthKey} to`,
                                        monthData[monthKey].contract
                                    )
                                } else if (
                                    contractType &&
                                    (contractType
                                        .toLowerCase()
                                        .includes("part-time") ||
                                        contractType
                                            .toLowerCase()
                                            .includes("part time"))
                                ) {
                                    monthData[monthKey].part_time += 1
                                    console.log(
                                        `Incremented part_time for ${monthKey} to`,
                                        monthData[monthKey].part_time
                                    )
                                }
                            }
                        }
                        if (record.date_end && record.state === "close") {
                            const endDateRecord = new Date(record.date_end)
                            console.log(
                                `Parsed contract date_end for ${monthKey}:`,
                                endDateRecord
                            )
                            if (endDateRecord <= monthEnd) {
                                monthData[monthKey].terminations += 1
                                console.log(
                                    `Incremented terminations for ${monthKey} to`,
                                    monthData[monthKey].terminations
                                )
                            }
                        }
                    })
                } catch (error) {
                    console.error(
                        `Error fetching hr.contract data for ${monthKey}:`,
                        error
                    )
                }
            }

            console.log(
                "Updating state.employee_inventory with monthData:",
                monthData
            )
            this.state.employee_inventory = {
                labels: filteredLabels,
                datasets: [
                    {
                        label: "Total Employees",
                        data: filteredLabels.map(
                            label => monthData[label]?.total || 0
                        ),
                        backgroundColor: "rgba(75, 192, 192, 0.6)",
                        borderColor: "rgba(75, 192, 192, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Male Employees",
                        data: filteredLabels.map(
                            label => monthData[label]?.male || 0
                        ),
                        backgroundColor: "rgba(54, 162, 235, 0.6)",
                        borderColor: "rgba(54, 162, 235, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Female Employees",
                        data: filteredLabels.map(
                            label => monthData[label]?.female || 0
                        ),
                        backgroundColor: "rgba(255, 99, 132, 0.6)",
                        borderColor: "rgba(255, 99, 132, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Additions",
                        data: filteredLabels.map(
                            label => monthData[label]?.additions || 0
                        ),
                        backgroundColor: "rgba(255, 206, 86, 0.6)",
                        borderColor: "rgba(255, 206, 86, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Terminations",
                        data: filteredLabels.map(
                            label => monthData[label]?.terminations || 0
                        ),
                        backgroundColor: "rgba(255, 159, 64, 0.6)",
                        borderColor: "rgba(255, 159, 64, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Permanent",
                        data: filteredLabels.map(
                            label => monthData[label]?.permanent || 0
                        ),
                        backgroundColor: "rgba(153, 102, 255, 0.6)",
                        borderColor: "rgba(153, 102, 255, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Contract",
                        data: filteredLabels.map(
                            label => monthData[label]?.contract || 0
                        ),
                        backgroundColor: "rgba(92, 255, 71, 0.6)",
                        borderColor: "rgb(62, 226, 29)",
                        borderWidth: 1,
                    },
                    {
                        label: "Part Time",
                        data: filteredLabels.map(
                            label => monthData[label]?.part_time || 0
                        ),
                        backgroundColor: "rgba(201, 203, 207, 0.6)",
                        borderColor: "rgba(201, 203, 207, 1)",
                        borderWidth: 1,
                    },
                ],
            }
            console.log(
                "Updated state.employee_inventory:",
                this.state.employee_inventory
            )
        } catch (error) {
            console.error("Error in getEmployeeInventoryData:", error)
            this.state.employee_inventory = {
                labels: [],
                datasets: [
                    {
                        label: "Total Employees",
                        data: [],
                        backgroundColor: "rgba(75, 192, 192, 0.6)",
                        borderColor: "rgba(75, 192, 192, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Male Employees",
                        data: [],
                        backgroundColor: "rgba(54, 162, 235, 0.6)",
                        borderColor: "rgba(54, 162, 235, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Female Employees",
                        data: [],
                        backgroundColor: "rgba(255, 99, 132, 0.6)",
                        borderColor: "rgba(255, 99, 132, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Additions",
                        data: [],
                        backgroundColor: "rgba(255, 206, 86, 0.6)",
                        borderColor: "rgba(255, 206, 86, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Terminations",
                        data: [],
                        backgroundColor: "rgba(255, 159, 64, 0.6)",
                        borderColor: "rgba(255, 159, 64, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Permanent",
                        data: [],
                        backgroundColor: "rgba(153, 102, 255, 0.6)",
                        borderColor: "rgba(153, 102, 255, 1)",
                        borderWidth: 1,
                    },
                    {
                        label: "Contract",
                        data: [],
                        backgroundColor: "rgba(92, 255, 71, 0.6)",
                        borderColor: "rgb(62, 226, 29)",
                        borderWidth: 1,
                    },
                    {
                        label: "Part Time",
                        data: [],
                        backgroundColor: "rgba(201, 203, 207, 0.6)",
                        borderColor: "rgba(201, 203, 207, 1)",
                        borderWidth: 1,
                    },
                ],
            }
            console.log(
                "Error occurred, set default state.employee_inventory:",
                this.state.employee_inventory
            )
        }
    }

    async getExpiringNewContract() {
        try {
            const today = new Date()
            const limitDate = new Date()
            limitDate.setDate(today.getDate() + 30)
            const formattedLimitDate = limitDate.toISOString().split("T")[0]

            let startDate, endDate
            if (!this.state.start_date) {
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
                endDate = today
            } else {
                startDate = new Date(this.state.start_date)
                endDate = this.state.end_date
                    ? new Date(this.state.end_date)
                    : new Date(today.getFullYear(), today.getMonth() + 1, 0)
            }

            if (isNaN(startDate.getTime())) {
                console.warn(
                    "Invalid start date, defaulting to start of current month"
                )
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
            }
            if (isNaN(endDate.getTime())) {
                console.warn("Invalid end date, defaulting to today")
                endDate = today
            }

            const formattedStartDate = startDate.toISOString().split("T")[0]
            const formattedEndDate = endDate.toISOString().split("T")[0]

            const domain = [
                ["date_end", "<=", formattedLimitDate],
                ["state", "in", ["open"]],
            ]
            const new_domain = [["state", "in", ["draft"]]]
            const before_start_domain = [
                ["state", "in", ["draft", "open"]],
                ["create_date", "<", formattedStartDate],
            ]

            const data = await this.orm.searchRead("hr.contract", new_domain, [
                "id",
            ])
            const expiring_contract = await this.orm.searchRead(
                "hr.contract",
                domain,
                ["id"]
            )
            const before_start_data = await this.orm.searchRead(
                "hr.contract",
                before_start_domain,
                ["id"]
            )

            const total_count = data.length + expiring_contract.length
            this.state.exparin_new_contract.value = total_count
            this.state.exparin_new_contract.current_month_count =
                total_count -
                (Array.isArray(before_start_data)
                    ? before_start_data.length
                    : 0)
        } catch (error) {
            console.error("Error in getExpiringNewContract:", error)
            this.state.exparin_new_contract.value = 0
            this.state.exparin_new_contract.current_month_count = 0
        }
    }

    async getLeaveRequest() {
        try {
            const today = new Date()
            let startDate, endDate
            if (!this.state.start_date) {
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
                endDate = today
            } else {
                startDate = new Date(this.state.start_date)
                endDate = this.state.end_date
                    ? new Date(this.state.end_date)
                    : new Date(today.getFullYear(), today.getMonth() + 1, 0)
            }

            if (isNaN(startDate.getTime())) {
                console.warn(
                    "Invalid start date, defaulting to start of current month"
                )
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
            }
            if (isNaN(endDate.getTime())) {
                console.warn("Invalid end date, defaulting to today")
                endDate = today
            }

            const formattedStartDate = startDate.toISOString().split("T")[0]
            const formattedEndDate = endDate.toISOString().split("T")[0]
            console.log("Date range for Leave Request:", {
                formattedStartDate,
                formattedEndDate,
            })

            const domain = [
                ["create_date", ">=", formattedStartDate],
                ["create_date", "<=", formattedEndDate],
                ["state", "in", ["confirm", "validate1"]],
            ]
            const before_start_domain = [
                ["create_date", "<", formattedStartDate],
                ["state", "in", ["confirm", "validate1"]],
            ]

            const data = await this.orm.searchRead("hr.leave", domain, ["id"])
            const before_start_data = await this.orm.searchRead(
                "hr.leave",
                before_start_domain,
                ["id"]
            )

            const total_count = Array.isArray(data) ? data.length : 0
            this.state.leave_request.value = total_count
            this.state.leave_request.current_month_count =
                total_count -
                (Array.isArray(before_start_data)
                    ? before_start_data.length
                    : 0)
        } catch (error) {
            console.error("Error in getLeaveRequest:", error)
            this.state.leave_request.value = 0
            this.state.leave_request.current_month_count = 0
        }
    }

    async getEmployee() {
        try {
            const totalEmployees = await this.orm.searchRead(
                "hr.employee",
                [],
                ["id"]
            )
            //   console.log("Total employees fetched ooooooooooooooooooooooooo:", totalEmployees)
            const totalCount = Array.isArray(totalEmployees)
                ? totalEmployees.length
                : 0

            // Handle start and end date with defaults
            const today = new Date()
            let startDate, endDate

            if (!this.state.start_date) {
                // Default to current month (first day of current month to today)
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
                endDate = today // Or use new Date(today.getFullYear(), today.getMonth() + 1, 0) for end of month
            } else {
                // Use provided start_date and end_date
                startDate = new Date(this.state.start_date)
                endDate = this.state.end_date
                    ? new Date(this.state.end_date)
                    : new Date(today.getFullYear(), today.getMonth() + 1, 0)
            }

            // Validate dates
            if (isNaN(startDate.getTime())) {
                console.warn(
                    "Invalid start date, defaulting to start of current month"
                )
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
            }
            if (isNaN(endDate.getTime())) {
                console.warn("Invalid end date, defaulting to today")
                endDate = today // Or end of current month
            }
            const formattedStartDate = startDate.toISOString().split("T")[0]
            const formattedEndDate = endDate.toISOString().split("T")[0]

            // Employees before start date
            const beforeStartDomain = [["create_date", "<", formattedStartDate]]
            const employeesBeforeStart = await this.orm.searchRead(
                "hr.employee",
                beforeStartDomain,
                ["id"]
            )
            // const beforeStartCount = Array.isArray(employeesBeforeStart) ? employeesBeforeStart.length : 0;

            // Employees between selected start_date and end_date
            const dateRangeDomain = [
                ["create_date", ">=", formattedStartDate],
                ["create_date", "<=", formattedEndDate],
            ]
            const employeesInRange = await this.orm.searchRead(
                "hr.employee",
                dateRangeDomain,
                ["id"]
            )
            const employeesInRangeCount = Array.isArray(employeesInRange)
                ? employeesInRange.length
                : 0
            // Previous month range (1 month before startDate to 1 day before startDate)
            const oneMonthBack = new Date(startDate)
            oneMonthBack.setMonth(oneMonthBack.getMonth() - 1)
            const oneDayBeforeStart = new Date(startDate)
            oneDayBeforeStart.setDate(oneDayBeforeStart.getDate() - 1)
            const formattedOneMonthBack = oneMonthBack
                .toISOString()
                .split("T")[0]
            const formattedOneDayBeforeStart = oneDayBeforeStart
                .toISOString()
                .split("T")[0]
            const previousMonthDomain = [
                ["create_date", ">=", formattedOneMonthBack],
                ["create_date", "<=", formattedOneDayBeforeStart],
            ]
            const previousMonthEmployees = await this.orm.searchRead(
                "hr.employee",
                previousMonthDomain,
                ["id"]
            )
            const previousMonthCount = Array.isArray(previousMonthEmployees)
                ? previousMonthEmployees.length
                : 0
            // Compute current_month_count = |employeesInRangeCount - previousMonthCount|
            const currentMonthCount = employeesInRangeCount - previousMonthCount
            // if (currentMonthCount < 0) {
            //     currentMonthCount = 0
            // }
            // Update state

            this.state.hr_employee.value = totalCount

            // this.state.hr_employee.percentage = totalCount > 0 ? ((beforeStartCount / totalCount) * 100).toFixed(2) : 0;
            this.state.hr_employee.current_month_count = currentMonthCount
        } catch (error) {
            this.state.hr_employee.value = 0
            // this.state.hr_employee.percentage = 0;
            this.state.hr_employee.current_month_count = 0
        }
    }
    async getAppraisal() {
        try {
            const today = new Date()
            const limitDate = new Date()
            limitDate.setDate(today.getDate() - 30)
            const formattedLimitDate = limitDate.toISOString().split("T")[0]

            let startDate, endDate
            if (!this.state.start_date) {
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
                endDate = today
            } else {
                startDate = new Date(this.state.start_date)
                endDate = this.state.end_date
                    ? new Date(this.state.end_date)
                    : new Date(today.getFullYear(), today.getMonth() + 1, 0)
            }

            if (isNaN(startDate.getTime())) {
                console.warn(
                    "Invalid start date, defaulting to start of current month"
                )
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
            }
            if (isNaN(endDate.getTime())) {
                console.warn("Invalid end date, defaulting to today")
                endDate = today
            }

            const formattedStartDate = startDate.toISOString().split("T")[0]
            const formattedEndDate = endDate.toISOString().split("T")[0]
            console.log("Date range for Appraisal:", {
                formattedStartDate,
                formattedEndDate,
            })

            const domain = [["create_date", ">=", formattedStartDate]]
            const before_start_domain = [
                ["create_date", "<", formattedStartDate],
            ]

            const data = await this.orm.searchRead("hr.appraisal", domain, [
                "id",
            ])
            const before_start_data = await this.orm.searchRead(
                "hr.appraisal",
                before_start_domain,
                ["id"]
            )

            const total_count = Array.isArray(data) ? data.length : 0
            this.state.appraisals.value = total_count
            this.state.appraisals.current_month_count =
                total_count -
                (Array.isArray(before_start_data)
                    ? before_start_data.length
                    : 0)
        } catch (error) {
            console.error("Error in getAppraisal:", error)
            this.state.appraisals.value = 0
            this.state.appraisals.current_month_count = 0
        }
    }

    async getResignation() {
        try {
            const today = new Date()
            const limitDate = new Date()
            limitDate.setDate(today.getDate() - 30)
            const formattedLimitDate = limitDate.toISOString().split("T")[0]

            let startDate, endDate
            if (!this.state.start_date) {
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
                endDate = today
            } else {
                startDate = new Date(this.state.start_date)
                endDate = this.state.end_date
                    ? new Date(this.state.end_date)
                    : new Date(today.getFullYear(), today.getMonth() + 1, 0)
            }

            if (isNaN(startDate.getTime())) {
                console.warn(
                    "Invalid start date, defaulting to start of current month"
                )
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
            }
            if (isNaN(endDate.getTime())) {
                console.warn("Invalid end date, defaulting to today")
                endDate = today
            }

            const formattedStartDate = startDate.toISOString().split("T")[0]
            const formattedEndDate = endDate.toISOString().split("T")[0]
            console.log("Date range for Resignation:", {
                formattedStartDate,
                formattedEndDate,
            })

            const domain = [["create_date", ">=", formattedStartDate]]
            const before_start_domain = [
                ["create_date", "<", formattedStartDate],
            ]

            const data = await this.orm.searchRead("hr.resignation", domain, [
                "id",
            ])
            const before_start_data = await this.orm.searchRead(
                "hr.resignation",
                before_start_domain,
                ["id"]
            )

            const total_count = Array.isArray(data) ? data.length : 0
            this.state.hr_resignation.value = total_count
            this.state.hr_resignation.current_month_count =
                total_count -
                (Array.isArray(before_start_data)
                    ? before_start_data.length
                    : 0)
        } catch (error) {
            console.error("Error in getResignation:", error)
            this.state.hr_resignation.value = 0
            this.state.hr_resignation.current_month_count = 0
        }
    }

    async getRecruitment() {
        try {
            const today = new Date()
            const limitDate = new Date()
            limitDate.setDate(today.getDate() - 30)
            const formattedLimitDate = limitDate.toISOString().split("T")[0]

            let startDate, endDate
            if (!this.state.start_date) {
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
                endDate = today
            } else {
                startDate = new Date(this.state.start_date)
                endDate = this.state.end_date
                    ? new Date(this.state.end_date)
                    : new Date(today.getFullYear(), today.getMonth() + 1, 0)
            }

            if (isNaN(startDate.getTime())) {
                console.warn(
                    "Invalid start date, defaulting to start of current month"
                )
                startDate = new Date(today.getFullYear(), today.getMonth(), 1)
            }
            if (isNaN(endDate.getTime())) {
                console.warn("Invalid end date, defaulting to today")
                endDate = today
            }

            const formattedStartDate = startDate.toISOString().split("T")[0]
            const formattedEndDate = endDate.toISOString().split("T")[0]
            console.log("Date range for Recruitment:", {
                formattedStartDate,
                formattedEndDate,
            })

            const domain = [
                ["create_date", ">=", formattedStartDate],
                ["state", "=", "open"],
            ]
            const before_start_domain = [
                ["create_date", "<", formattedStartDate],
                ["state", "=", "open"],
            ]

            const data = await this.orm.searchRead("hr.contract", domain, [
                "id",
            ])
            const before_start_data = await this.orm.searchRead(
                "hr.contract",
                before_start_domain,
                ["id"]
            )

            const total_count = Array.isArray(data) ? data.length : 0
            this.state.recruitment.value = total_count
            this.state.recruitment.current_month_count =
                total_count -
                (Array.isArray(before_start_data)
                    ? before_start_data.length
                    : 0)
        } catch (error) {
            console.error("Error in getRecruitment:", error)
            this.state.recruitment.value = 0
            this.state.recruitment.current_month_count = 0
        }
    }

    async getMonthlyPayrollData() {
        try {
            const today = new Date()
            const currentYear = today.getFullYear()

            const domain = [
                ["code", "=", "GROSS"],
                ["date_from", ">=", `${currentYear}-01-01`],
                ["date_from", "<=", `${currentYear}-12-31`],
            ]

            const data = await this.orm.searchRead("hr.payslip.line", domain, [
                "total",
                "slip_id",
                "date_from",
            ])
            console.log("Payroll data fetched gggg:", data)

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

            data.forEach(record => {
                if (record["date_from"]) {
                    const date = new Date(record["date_from"])
                    const month = date.getMonth() // 0–11
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

                    if (monthKey in monthData) {
                        monthData[monthKey] += record.total || 0
                    }
                }
            })

            this.state.payroll_by_month = {
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
                        label: "Gross Payroll by Month",
                        data: Object.values(monthData),
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
                        borderWidth: 1,
                    },
                ],
            }
        } catch (error) {
            console.error("Error fetching data:", error)
        }
    }

    async getEmployeeByDepartmentData() {
        try {
            const data = await this.orm.searchRead(
                "hr.employee",
                [["active", "in", [true, false]]],
                ["department_id"],
                { context: { active_test: false } }
            )

            const departmentCounts = {}
            const departmentLabels = []

            data.forEach(record => {
                const dept = record.department_id
                if (dept && dept.length === 2) {
                    const [id, name] = dept
                    const parts = name.split(" / ")
                    const finalDept = parts[parts.length - 1].trim()
                    if (!departmentCounts[finalDept]) {
                        departmentCounts[finalDept] = 0
                        departmentLabels.push(finalDept)
                    }
                    departmentCounts[finalDept]++
                }
            })

            this.state.employee_by_department = {
                labels: departmentLabels,
                datasets: [
                    {
                        label: "Employees per Department",
                        data: departmentLabels.map(
                            label => departmentCounts[label]
                        ),
                        backgroundColor: departmentLabels.map(
                            (_, i) => `hsl(${(i * 40) % 360}, 70%, 60%)`
                        ),
                        borderColor: departmentLabels.map(
                            (_, i) => `hsl(${(i * 40) % 360}, 70%, 40%)`
                        ),
                        borderWidth: 1,
                    },
                ],
            }
        } catch (error) {
            console.error("Error fetching employee data:", error)
        }
    }

    async getAppraisalByDepartmentData() {
        try {
            const data = await this.orm.searchRead(
                "hr.appraisal",
                [],
                ["department_id"]
            )

            const departmentCounts = {}
            const departmentLabels = []

            data.forEach(record => {
                const dept = record.department_id
                if (dept && dept.length === 2) {
                    const [id, name] = dept
                    if (!departmentCounts[name]) {
                        departmentCounts[name] = 0
                        departmentLabels.push(name)
                    }
                    departmentCounts[name]++
                }
            })

            this.state.appraisal_by_department = {
                labels: departmentLabels,
                datasets: [
                    {
                        label: "Appraisal per Department",
                        data: departmentLabels.map(
                            label => departmentCounts[label]
                        ),
                        backgroundColor: departmentLabels.map(
                            (_, i) => `hsl(${(i * 40) % 360}, 70%, 60%)`
                        ),
                        borderColor: departmentLabels.map(
                            (_, i) => `hsl(${(i * 40) % 360}, 70%, 40%)`
                        ),
                        borderWidth: 1,
                    },
                ],
            }
        } catch (error) {
            console.error("Error fetching appraisal data:", error)
        }
    }
}

MainDashboard.template = "hr_dashboard.MainDashboard"
MainDashboard.components = { DashboardCard, ChartRenderer }

registry
    .category("actions")
    .add("hr_dashboard.dashboard_main_view", MainDashboard)
