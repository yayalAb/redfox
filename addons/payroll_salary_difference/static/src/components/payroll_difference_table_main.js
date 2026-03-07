/** @odoo-module **/

import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"

const { Component, onWillStart, useState } = owl

export class PayrollDifferenceTable extends Component {
    setup() {
        this.state = useState({
            employees: [],
            salary_rules: [],
            data: {},
            batch1: null,
            batch2: null,
            available_batches: [],
            selected_batch1_id: null,
            selected_batch2_id: null,
            loading: true,
            currentPage: 1,
            itemsPerPage: 50,
            searchTerm: '',
            showModal: false,
            modalData: null,
        })

        this.orm = useService("orm")
        this.action = useService("action")

        onWillStart(async () => {
            await this.loadBatches()
            // Auto-load data if batches are selected
            if (this.state.selected_batch1_id && this.state.selected_batch2_id) {
                await this.loadData()
            }
        })

        this.onBatch1Change = async (ev) => {
            const batchId = ev.target.value ? parseInt(ev.target.value) : null
            this.state.selected_batch1_id = batchId
            await this.loadData()
        }

        this.onBatch2Change = async (ev) => {
            const batchId = ev.target.value ? parseInt(ev.target.value) : null
            this.state.selected_batch2_id = batchId
            await this.loadData()
        }

        this.loadBatches = async () => {
            try {
                this.state.loading = true
                const batches = await this.orm.call(
                    "hr.payslip.run",
                    "get_available_batches",
                    [],
                    {}
                )
                this.state.available_batches = batches || []
                
                // Set default to two most recent batches
                if (batches && batches.length >= 2) {
                    this.state.selected_batch1_id = batches[0].id
                    this.state.selected_batch2_id = batches[1].id
                } else if (batches && batches.length === 1) {
                    this.state.selected_batch1_id = batches[0].id
                }
            } catch (error) {
                console.error("Error loading batches:", error)
                this.state.available_batches = []
            } finally {
                this.state.loading = false
            }
        }

        this.loadData = async () => {
            // Only load if both batches are selected
            if (!this.state.selected_batch1_id || !this.state.selected_batch2_id) {
                this.state.employees = []
                this.state.salary_rules = []
                this.state.data = {}
                this.state.batch1 = null
                this.state.batch2 = null
                return
            }
            
            this.state.loading = true
            try {
                const data = await this.orm.call(
                    "hr.payslip.run",
                    "get_payroll_difference_data",
                    [this.state.selected_batch1_id, this.state.selected_batch2_id],
                    {}
                )
                
                if (data.error) {
                    this.state.employees = []
                    this.state.salary_rules = []
                    this.state.data = {}
                    this.state.batch1 = null
                    this.state.batch2 = null
                    alert(data.error)
                } else {
                    this.state.employees = data.employees || []
                    this.state.salary_rules = data.salary_rules || []
                    this.state.data = data.data || {}
                    this.state.batch1 = data.batch1 || null
                    this.state.batch2 = data.batch2 || null
                    this.state.currentPage = 1 // Reset to first page when new data loads
                }
            } catch (error) {
                console.error("Error loading payroll difference data:", error)
                this.state.employees = []
                this.state.salary_rules = []
                this.state.data = {}
                this.state.batch1 = null
                this.state.batch2 = null
            } finally {
                this.state.loading = false
            }
        }

        this.getAmount = (employeeId, ruleIdOrCode, batch) => {
            const empData = this.state.data[employeeId]
            if (!empData) return null
            
            // Try to find by code first (new format), then by id (backward compatibility)
            const rule = this.state.salary_rules.find(r => r.id === ruleIdOrCode || r.code === ruleIdOrCode)
            const lookupKey = rule ? rule.code : ruleIdOrCode
            
            if (empData[lookupKey] && empData[lookupKey][batch] !== undefined) {
                return empData[lookupKey][batch]
            }
            return null
        }

        this.calculateDifference = (employeeId, ruleId) => {
            const batch1Amount = this.getAmount(employeeId, ruleId, 'batch1')
            const batch2Amount = this.getAmount(employeeId, ruleId, 'batch2')
            
            if (batch1Amount === null || batch2Amount === null) {
                return null
            }
            
            // Calculate difference as: batch1 - batch2
            const diff = batch1Amount - batch2Amount
            
            // Return null if difference is 0, so it displays as "-"
            if (diff === 0 || Math.abs(diff) < 0.01) {
                return null
            }
            
            return diff
        }

        this.formatCurrency = (value) => {
            if (value === null || value === undefined) return '--'
            // Format with thousand separators
            return value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
        }

        this.getDifferenceClass = (difference) => {
            if (difference === null || difference === undefined) return ''
            if (difference > 0) return 'text-success'
            if (difference < 0) return 'text-danger'
            return 'text-muted'
        }

        this.calculateEmployeeTotal = (employeeId) => {
            let total = 0
            let hasData = false
            this.state.salary_rules.forEach(rule => {
                const diff = this.calculateDifference(employeeId, rule.id)
                if (diff !== null && diff !== undefined) {
                    total += diff
                    hasData = true
                }
            })
            return hasData ? total : null
        }

        this.calculateRuleTotal = (ruleId) => {
            let total = 0
            let hasData = false
            const employeesWithDiff = this.getEmployeesWithDifference()
            employeesWithDiff.forEach(employee => {
                const diff = this.calculateDifference(employee.id, ruleId)
                if (diff !== null && diff !== undefined) {
                    total += diff
                    hasData = true
                }
            })
            return hasData ? total : null
        }

        this.calculateGrandTotal = () => {
            let total = 0
            let hasData = false
            const employeesWithDiff = this.getEmployeesWithDifference()
            employeesWithDiff.forEach(employee => {
                const empTotal = this.calculateEmployeeTotal(employee.id)
                if (empTotal !== null && empTotal !== undefined) {
                    total += empTotal
                    hasData = true
                }
            })
            return hasData ? total : null
        }

        this.onViewBatchClick = (batchId) => {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Payroll Batch",
                res_model: "hr.payslip.run",
                view_mode: "form",
                views: [[false, "form"]],
                target: "current",
                res_id: batchId,
            })
        }

        this.getEmployeesWithDifference = () => {
            let filtered = this.state.employees.filter(employee => {
                // Check if employee has at least one non-null difference
                return this.state.salary_rules.some(rule => {
                    const diff = this.calculateDifference(employee.id, rule.id)
                    return diff !== null && diff !== undefined && diff !== 0
                })
            })
            
            // Filter by search term if provided (search by name or employee ID)
            if (this.state.searchTerm && this.state.searchTerm.trim() !== '') {
                const searchLower = this.state.searchTerm.toLowerCase().trim()
                filtered = filtered.filter(employee => {
                    const nameMatch = employee.name.toLowerCase().includes(searchLower)
                    const idMatch = employee.employee_id && employee.employee_id.toLowerCase().includes(searchLower)
                    return nameMatch || idMatch
                })
            }
            
            return filtered
        }

        this.onSearchChange = (ev) => {
            this.state.searchTerm = ev.target.value
            this.state.currentPage = 1 // Reset to first page when search changes
        }

        this.getAmountDetails = (employeeId, ruleIdOrCode, batch) => {
            const empData = this.state.data[employeeId]
            if (!empData) return null
            
            // Try to find by code first (new format), then by id (backward compatibility)
            const rule = this.state.salary_rules.find(r => r.id === ruleIdOrCode || r.code === ruleIdOrCode)
            const lookupKey = rule ? rule.code : ruleIdOrCode
            
            if (empData[lookupKey] && empData[lookupKey][batch + '_details']) {
                return empData[lookupKey][batch + '_details']
            }
            return null
        }

        this.onCellClick = (employeeId, ruleId) => {
            const employee = this.state.employees.find(emp => emp.id === employeeId)
            const rule = this.state.salary_rules.find(r => r.id === ruleId)
            const batch1Amount = this.getAmount(employeeId, ruleId, 'batch1')
            const batch2Amount = this.getAmount(employeeId, ruleId, 'batch2')
            const diff = this.calculateDifference(employeeId, ruleId)
            const batch1Details = this.getAmountDetails(employeeId, ruleId, 'batch1')
            const batch2Details = this.getAmountDetails(employeeId, ruleId, 'batch2')
            
            this.state.modalData = {
                employee: employee,
                rule: rule,
                batch1Amount: batch1Amount,
                batch2Amount: batch2Amount,
                difference: diff,
                batch1Name: this.state.batch1 ? this.state.batch1.name : '',
                batch2Name: this.state.batch2 ? this.state.batch2.name : '',
                batch1Details: batch1Details,
                batch2Details: batch2Details,
                variableBreakdown: null,
                variableBreakdownLoading: true,
            }
            this.state.showModal = true

            // Fetch variable breakdown for formula display (contract wage / active rates / etc.)
            this.orm.call(
                "hr.payslip.run",
                "get_salary_rule_variable_breakdown",
                [this.state.selected_batch1_id, this.state.selected_batch2_id, employeeId, ruleId],
                {}
            ).then((res) => {
                if (this.state.modalData) {
                    this.state.modalData.variableBreakdown = res || null
                    this.state.modalData.variableBreakdownLoading = false
                }
            }).catch((err) => {
                console.error("Failed to load variable breakdown:", err)
                if (this.state.modalData) {
                    this.state.modalData.variableBreakdown = null
                    this.state.modalData.variableBreakdownLoading = false
                }
            })
        }

        this.closeModal = () => {
            this.state.showModal = false
            this.state.modalData = null
        }

        this.onHeaderClick = (ruleId) => {
            const rule = this.state.salary_rules.find(r => r.id === ruleId)
            
            this.state.modalData = {
                rule: rule,
                isHeaderClick: true,
            }
            this.state.showModal = true
        }

        this.getPaginatedEmployees = () => {
            const employeesWithDiff = this.getEmployeesWithDifference()
            const start = (this.state.currentPage - 1) * this.state.itemsPerPage
            const end = start + this.state.itemsPerPage
            return employeesWithDiff.slice(start, end)
        }

        this.getTotalPages = () => {
            return Math.ceil(this.state.employees.length / this.state.itemsPerPage)
        }

        this.getPageNumbers = () => {
            const totalPages = this.getTotalPages()
            const currentPage = this.state.currentPage
            const pages = []
            
            let startPage = Math.max(1, currentPage - 2)
            let endPage = Math.min(totalPages, currentPage + 2)
            
            if (startPage > 1) {
                pages.push({ type: 'number', value: 1 })
                if (startPage > 2) {
                    pages.push({ type: 'ellipsis' })
                }
            }
            
            for (let i = startPage; i <= endPage; i++) {
                pages.push({ type: 'number', value: i })
            }
            
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    pages.push({ type: 'ellipsis' })
                }
                pages.push({ type: 'number', value: totalPages })
            }
            
            return pages
        }

        this.goToPage = (page) => {
            const totalPages = this.getTotalPages()
            if (page >= 1 && page <= totalPages) {
                this.state.currentPage = page
            }
        }

        this.previousPage = () => {
            if (this.state.currentPage > 1) {
                this.state.currentPage = this.state.currentPage - 1
            }
        }

        this.nextPage = () => {
            const totalPages = this.getTotalPages()
            if (this.state.currentPage < totalPages) {
                this.state.currentPage = this.state.currentPage + 1
            }
        }

        this.onItemsPerPageChange = (ev) => {
            this.state.itemsPerPage = parseInt(ev.target.value)
            this.state.currentPage = 1 // Reset to first page
        }

        this.onExportExcelClick = () => {
            // Prepare data for Excel export
            const rows = []
            
            // Header row
            const headerRow = ['S.No', 'Employee']
            this.state.salary_rules.forEach(rule => {
                headerRow.push(`${rule.name} (Diff)`)
            })
            rows.push(headerRow)
            
            // Data rows - only employees with differences
            const employeesWithDiff = this.getEmployeesWithDifference()
            employeesWithDiff.forEach((employee, index) => {
                const row = [index + 1, employee.name]
                
                this.state.salary_rules.forEach(rule => {
                    const diff = this.calculateDifference(employee.id, rule.id)
                    row.push(diff !== null ? diff.toFixed(2) : '-')
                })
                
                rows.push(row)
            })
            
            // Convert to CSV
            const csvContent = rows.map(row => 
                row.map(cell => `"${cell}"`).join(',')
            ).join('\n')
            
            // Create blob and download
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
            const link = document.createElement('a')
            const url = URL.createObjectURL(blob)
            link.setAttribute('href', url)
            link.setAttribute('download', `payroll_salary_difference_${new Date().toISOString().split('T')[0]}.csv`)
            link.style.visibility = 'hidden'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
        }
    }

    static template = "payroll_salary_difference.PayrollDifferenceTable"
}

registry.category("actions").add("payroll_salary_difference.payroll_difference_table_action", PayrollDifferenceTable)

