/** @odoo-module **/

import { registry } from "@web/core/registry"
import { DashboardCard } from "./dashboard_card/dashboard_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { useService } from "@web/core/utils/hooks"
import { user } from "@web/core/user"

const { Component, onWillStart, useState } = owl

export class MainDashboard extends Component {
    setup() {
        this.state = useState({
            start_date: "",
            end_date: "",
            store_request: { value: 0, current_month_count: 0 },
            purchase_request: { value: 0, current_month_count: 0 },
            payment_request: { value: 0, current_month_count: 0 },
            leave_request: { value: 0, current_month_count: 0 },
            fleet_request: { value: 0, current_month_count: 0 },
            job_requisition: { value: 0, current_month_count: 0 },
            // Status breakdowns
            store_request_status: {
                draft: 0,
                submitted: 0,
                approved: 0,
                issued: 0,
                rejected: 0,
            },
            purchase_request_status: {
                draft: 0,
                submitted: 0,
                approved: 0,
                evaluation: 0,
                ordered: 0,
                rejected: 0,
            },
            payment_request_status: {
                draft: 0,
                submit: 0,
                verify: 0,
                authorize: 0,
                approve: 0,
                post: 0,
                cancel: 0,
            },
            leave_request_status: {
                draft: 0,
                confirm: 0,
                validate: 0,
                refuse: 0,
            },
            fleet_request_status: {
                draft: 0,
                in_review: 0,
                approved: 0,
                authorize: 0,
                cancel: 0,
                rejected: 0,
            },
            job_requisition_status: {
                draft: 0,
                submitted: 0,
                reviewed: 0,
                approved: 0,
                authorized: 0,
                published: 0,
                rejected: 0,
            },
            // Chart data for status breakdowns
            store_request_chart: {
                labels: [],
                datasets: [{
                    label: "Store Requests",
                    data: [],
                    backgroundColor: [],
                }],
            },
            purchase_request_chart: {
                labels: [],
                datasets: [{
                    label: "Purchase Requests",
                    data: [],
                    backgroundColor: [],
                }],
            },
            payment_request_chart: {
                labels: [],
                datasets: [{
                    label: "Payment Requests",
                    data: [],
                    backgroundColor: [],
                }],
            },
            leave_request_chart: {
                labels: [],
                datasets: [{
                    label: "Leave Requests",
                    data: [],
                    backgroundColor: [],
                }],
            },
            fleet_request_chart: {
                labels: [],
                datasets: [{
                    label: "Fleet Requests",
                    data: [],
                    backgroundColor: [],
                }],
            },
            job_requisition_chart: {
                labels: [],
                datasets: [{
                    label: "Job Requisitions",
                    data: [],
                    backgroundColor: [],
                }],
            },
        })

        this.orm = useService("orm")
        this.action = useService("action")

        onWillStart(async () => {
            await this.refreshData()
        })

        // Click handlers for cards
        this.onStoreRequestClick = () => {
            this.openFilteredView('store.request', 'requested_by', 'Store Requests')
        }

        this.onPurchaseRequestClick = () => {
            this.openFilteredView('supplies.rfp', 'create_uid', 'Purchase Requests', true)
        }

        this.onPaymentRequestClick = () => {
            this.openFilteredView('hr.expense.sheet', 'employee_id', 'Payment Requests')
        }

        this.onLeaveRequestClick = () => {
            this.openFilteredView('hr.leave', 'employee_id', 'Leave Requests')
        }

        this.onFleetRequestClick = () => {
            this.openFilteredView('fleet.vehicle.request', 'user_id', 'Fleet Requests', true)
        }

        this.onJobRequisitionClick = () => {
            this.openFilteredView('hr.job.requisition', 'requested_by', 'Job Requisitions', true)
        }

        // Bind refresh method for template
        this.refreshData = this.refreshData.bind(this)
    }

    async getSubordinateEmployeeIds(employeeId) {
        if (!employeeId) return []
        
        const employeeIds = [employeeId]
        const subordinates = await this.orm.search('hr.employee', [['parent_id', '=', employeeId]], {})
        
        for (const subordinateId of subordinates) {
            const childIds = await this.getSubordinateEmployeeIds(subordinateId)
            employeeIds.push(...childIds)
        }
        
        return employeeIds
    }

    async getSubordinateUserIds(employeeId) {
        const employeeIds = await this.getSubordinateEmployeeIds(employeeId)
        const employees = await this.orm.read('hr.employee', employeeIds, ['user_id'], {})
        const userIds = employees
            .map(emp => emp.user_id && emp.user_id[0])
            .filter(uid => uid)
        return userIds
    }

    async getCurrentEmployee() {
        // Get current user ID from user service
        const userId = user.userId
        if (!userId) {
            console.warn("No user ID found")
            return null
        }
        const employees = await this.orm.searchRead(
            'hr.employee',
            [['user_id', '=', userId]],
            ['id'],
            { limit: 1 }
        )
        return employees.length > 0 ? employees[0].id : null
    }

    async openFilteredView(model, field, name, useUserId = false) {
        const currentEmployee = await this.getCurrentEmployee()
        if (!currentEmployee) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: name,
                res_model: model,
                view_mode: "list,form",
                target: "current",
            })
            return
        }

        let domain = []
        if (useUserId) {
            const userIds = await this.getSubordinateUserIds(currentEmployee)
            domain = [[field, 'in', userIds]]
        } else {
            const employeeIds = await this.getSubordinateEmployeeIds(currentEmployee)
            domain = [[field, 'in', employeeIds]]
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: model,
            view_mode: "list,form",
            target: "current",
            domain: domain,
        })
    }

    async refreshData() {
        const currentEmployee = await this.getCurrentEmployee()
        if (!currentEmployee) {
            console.warn("No employee record found for current user")
            return
        }

        const employeeIds = await this.getSubordinateEmployeeIds(currentEmployee)
        const userIds = await this.getSubordinateUserIds(currentEmployee)

        await Promise.all([
            this.getStoreRequestData(employeeIds),
            this.getPurchaseRequestData(userIds),
            this.getPaymentRequestData(employeeIds),
            this.getLeaveRequestData(employeeIds),
            this.getFleetRequestData(userIds),
            this.getJobRequisitionData(userIds),
        ])
    }

    async getStoreRequestData(employeeIds) {
        try {
            const domain = [['requested_by', 'in', employeeIds]]
            const allRequests = await this.orm.searchRead('store.request', domain, ['state'], {})
            
            const statusCounts = {
                draft: 0,
                submitted: 0,
                approved: 0,
                issue: 0,
                rejected: 0,
            }
            
            allRequests.forEach(req => {
                if (statusCounts.hasOwnProperty(req.state)) {
                    statusCounts[req.state]++
                }
            })

            this.state.store_request.value = allRequests.length
            this.state.store_request_status = statusCounts
            this.state.store_request.current_month_count = allRequests.length
            
            // Update chart data
            this.state.store_request_chart = {
                labels: ['Draft', 'Submitted', 'Approved', 'Issued', 'Rejected'],
                datasets: [{
                    label: "Store Requests",
                    data: [
                        statusCounts.draft,
                        statusCounts.submitted,
                        statusCounts.approved,
                        statusCounts.issue,
                        statusCounts.rejected
                    ],
                    backgroundColor: [
                        'rgba(108, 117, 125, 0.6)',
                        'rgba(0, 123, 255, 0.6)',
                        'rgba(40, 167, 69, 0.6)',
                        'rgba(23, 162, 184, 0.6)',
                        'rgba(220, 53, 69, 0.6)'
                    ],
                }],
            }
        } catch (error) {
            console.error("Error fetching store request data:", error)
        }
    }

    async getPurchaseRequestData(userIds) {
        try {
            const domain = [['create_uid', 'in', userIds]]
            const allRequests = await this.orm.searchRead('supplies.rfp', domain, ['state'], {})
            
            const statusCounts = {
                draft: 0,
                submitted: 0,
                approved: 0,
                f_approved: 0,
                evaluation: 0,
                ordered: 0,
                rejected: 0,
            }
            
            allRequests.forEach(req => {
                if (req.state === 'approved' || req.state === 'f_approved') {
                    statusCounts.approved++
                } else if (statusCounts.hasOwnProperty(req.state)) {
                    statusCounts[req.state]++
                }
            })

            this.state.purchase_request.value = allRequests.length
            this.state.purchase_request_status = statusCounts
            this.state.purchase_request.current_month_count = allRequests.length
            
            // Update chart data
            this.state.purchase_request_chart = {
                labels: ['Draft', 'Submitted', 'Approved', 'Evaluation', 'Ordered', 'Rejected'],
                datasets: [{
                    label: "Purchase Requests",
                    data: [
                        statusCounts.draft,
                        statusCounts.submitted,
                        statusCounts.approved,
                        statusCounts.evaluation,
                        statusCounts.ordered,
                        statusCounts.rejected
                    ],
                    backgroundColor: [
                        'rgba(108, 117, 125, 0.6)',
                        'rgba(0, 123, 255, 0.6)',
                        'rgba(40, 167, 69, 0.6)',
                        'rgba(255, 193, 7, 0.6)',
                        'rgba(23, 162, 184, 0.6)',
                        'rgba(220, 53, 69, 0.6)'
                    ],
                }],
            }
        } catch (error) {
            console.error("Error fetching purchase request data:", error)
        }
    }

    async getPaymentRequestData(employeeIds) {
        try {
            const domain = [['employee_id', 'in', employeeIds]]
            const allRequests = await this.orm.searchRead('hr.expense.sheet', domain, ['state'], {})
            
            const statusCounts = {
                draft: 0,
                submit: 0,
                verify: 0,
                authorize: 0,
                approve: 0,
                post: 0,
                cancel: 0,
            }
            
            allRequests.forEach(req => {
                if (statusCounts.hasOwnProperty(req.state)) {
                    statusCounts[req.state]++
                }
            })

            this.state.payment_request.value = allRequests.length
            this.state.payment_request_status = statusCounts
            this.state.payment_request.current_month_count = allRequests.length
            
            // Update chart data
            this.state.payment_request_chart = {
                labels: ['Draft', 'Submitted', 'To Verify', 'Authorized', 'Approved', 'Posted', 'Cancelled'],
                datasets: [{
                    label: "Payment Requests",
                    data: [
                        statusCounts.draft,
                        statusCounts.submit,
                        statusCounts.verify,
                        statusCounts.authorize,
                        statusCounts.approve,
                        statusCounts.post,
                        statusCounts.cancel
                    ],
                    backgroundColor: [
                        'rgba(108, 117, 125, 0.6)',
                        'rgba(0, 123, 255, 0.6)',
                        'rgba(255, 193, 7, 0.6)',
                        'rgba(111, 66, 193, 0.6)',
                        'rgba(40, 167, 69, 0.6)',
                        'rgba(23, 162, 184, 0.6)',
                        'rgba(220, 53, 69, 0.6)'
                    ],
                }],
            }
        } catch (error) {
            console.error("Error fetching payment request data:", error)
        }
    }

    async getLeaveRequestData(employeeIds) {
        try {
            const domain = [['employee_id', 'in', employeeIds]]
            const allRequests = await this.orm.searchRead('hr.leave', domain, ['state'], {})
            
            const statusCounts = {
                draft: 0,
                confirm: 0,
                validate: 0,
                validate1: 0,
                refuse: 0,
            }
            
            allRequests.forEach(req => {
                if (req.state === 'validate' || req.state === 'validate1') {
                    statusCounts.validate++
                } else if (statusCounts.hasOwnProperty(req.state)) {
                    statusCounts[req.state]++
                }
            })

            this.state.leave_request.value = allRequests.length
            this.state.leave_request_status = statusCounts
            this.state.leave_request.current_month_count = allRequests.length
            
            // Update chart data
            this.state.leave_request_chart = {
                labels: ['Draft', 'Confirmed', 'Validated', 'Refused'],
                datasets: [{
                    label: "Leave Requests",
                    data: [
                        statusCounts.draft,
                        statusCounts.confirm,
                        statusCounts.validate,
                        statusCounts.refuse
                    ],
                    backgroundColor: [
                        'rgba(108, 117, 125, 0.6)',
                        'rgba(0, 123, 255, 0.6)',
                        'rgba(40, 167, 69, 0.6)',
                        'rgba(220, 53, 69, 0.6)'
                    ],
                }],
            }
        } catch (error) {
            console.error("Error fetching leave request data:", error)
        }
    }

    async getFleetRequestData(userIds) {
        try {
            const domain = [['user_id', 'in', userIds]]
            const allRequests = await this.orm.searchRead('fleet.vehicle.request', domain, ['state'], {})
            
            const statusCounts = {
                draft: 0,
                in_review: 0,
                approved: 0,
                authorize: 0,
                cancel: 0,
                rejected: 0,
            }
            
            allRequests.forEach(req => {
                if (statusCounts.hasOwnProperty(req.state)) {
                    statusCounts[req.state]++
                }
            })

            this.state.fleet_request.value = allRequests.length
            this.state.fleet_request_status = statusCounts
            this.state.fleet_request.current_month_count = allRequests.length
            
            // Update chart data
            this.state.fleet_request_chart = {
                labels: ['Draft', 'Submitted', 'Approved', 'Authorized', 'Cancelled', 'Rejected'],
                datasets: [{
                    label: "Fleet Requests",
                    data: [
                        statusCounts.draft,
                        statusCounts.in_review,
                        statusCounts.approved,
                        statusCounts.authorize,
                        statusCounts.cancel,
                        statusCounts.rejected
                    ],
                    backgroundColor: [
                        'rgba(108, 117, 125, 0.6)',
                        'rgba(0, 123, 255, 0.6)',
                        'rgba(40, 167, 69, 0.6)',
                        'rgba(111, 66, 193, 0.6)',
                        'rgba(255, 193, 7, 0.6)',
                        'rgba(220, 53, 69, 0.6)'
                    ],
                }],
            }
        } catch (error) {
            console.error("Error fetching fleet request data:", error)
        }
    }

    async getJobRequisitionData(userIds) {
        try {
            const domain = [['requested_by', 'in', userIds]]
            const allRequests = await this.orm.searchRead('hr.job.requisition', domain, ['state'], {})
            
            const statusCounts = {
                draft: 0,
                submitted: 0,
                reviewed: 0,
                approved: 0,
                authorized: 0,
                published: 0,
                rejected: 0,
            }
            
            allRequests.forEach(req => {
                if (statusCounts.hasOwnProperty(req.state)) {
                    statusCounts[req.state]++
                }
            })

            this.state.job_requisition.value = allRequests.length
            this.state.job_requisition_status = statusCounts
            this.state.job_requisition.current_month_count = allRequests.length
            
            // Update chart data
            this.state.job_requisition_chart = {
                labels: ['Draft', 'Submitted', 'Reviewed', 'Approved', 'Authorized', 'Published', 'Rejected'],
                datasets: [{
                    label: "Job Requisitions",
                    data: [
                        statusCounts.draft,
                        statusCounts.submitted,
                        statusCounts.reviewed,
                        statusCounts.approved,
                        statusCounts.authorized,
                        statusCounts.published,
                        statusCounts.rejected
                    ],
                    backgroundColor: [
                        'rgba(108, 117, 125, 0.6)',
                        'rgba(0, 123, 255, 0.6)',
                        'rgba(255, 193, 7, 0.6)',
                        'rgba(40, 167, 69, 0.6)',
                        'rgba(111, 66, 193, 0.6)',
                        'rgba(23, 162, 184, 0.6)',
                        'rgba(220, 53, 69, 0.6)'
                    ],
                }],
            }
        } catch (error) {
            console.error("Error fetching job requisition data:", error)
        }
    }

    async onStartDateChange(ev) {
        this.state.start_date = ev.target.value
        await this.refreshData()
    }

    async onEndDateChange(ev) {
        this.state.end_date = ev.target.value
        await this.refreshData()
    }

}

MainDashboard.template = "manager_dashboard.MainDashboard"
MainDashboard.components = { DashboardCard, ChartRenderer }

registry
    .category("actions")
    .add("manager_dashboard.dashboard_main_view", MainDashboard)

