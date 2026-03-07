# -*- coding: utf-8 -*-

from odoo import models, fields, api


# class Department(models.Model):
#     _inherit = 'hr.department'

#     cost_center = fields.Char(string='Cost Center')


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    duplicate_bank_partner_ids = fields.Many2many(
        'res.partner')


class PayslipWithCustomColumns(models.Model):
    _inherit = 'hr.payslip'

    basic_wage = fields.Monetary(
        string="Basic Salary")
    gross_wage = fields.Monetary(
        string="Gross Earning")
    net_wage = fields.Monetary(
        string="Net Pay")
    sequence_no = fields.Integer(
        string='S.No.', compute='_compute_sequence_no')
    employee_id = fields.Many2one(
        string="Employee Name")

    employee_id_no = fields.Char(
        string="Employee ID", related='employee_id.identification_id', store=True, readonly=True)

    core_department_id = fields.Many2one(
        string="Core Department", related="employee_id.cost_center_id", store=True, readonly=True)

    branch_id = fields.Many2one(
        string="Branch", related="employee_id.brach_id", store=True, readonly=True)
    branch_name = fields.Char(related='branch_id.name',
                              string="Branch", store=True)
    employee_name = fields.Char(
        string="Employee Full Name", related='employee_id.name', store=True)

    _order = 'branch_name asc, employee_id_no asc, employee_name asc, date_from desc'

    @api.depends()
    def _compute_sequence_no(self):
        for index, record in enumerate(self, start=1):
            record.sequence_no = index
    hr_contract_start = fields.Date(
        string="Start Date", related='contract_id.date_start', store=True, readonly=True)
    hr_contract_end = fields.Date(
        string="End Date", related='contract_id.date_end', store=True, readonly=True)
    hr_contract_start_formatted = fields.Char(
        string="Formatted Start Date", compute='_compute_formatted_date')

    def _compute_formatted_date(self):
        for rec in self:
            if rec.hr_contract_start:
                rec.hr_contract_start_formatted = rec.hr_contract_start.strftime(
                    '%d/%m/%Y')
            else:
                rec.hr_contract_start_formatted = ''

    attachment_salary = fields.Monetary(
        string="Attachment of Salary", compute='_calculate_all_rule_amounts', store=True)
    assignment_salary = fields.Monetary(
        string="Assignment of Salary", compute='_calculate_all_rule_amounts', store=True)
    child_support = fields.Monetary(
        string="Child Support", compute='_calculate_all_rule_amounts', store=True)
    deduction = fields.Monetary(
        string="Total Deduction", compute='_calculate_all_rule_amounts', store=True)
    pension = fields.Monetary(
        string="Pension Contribution 7%", compute='_calculate_all_rule_amounts', store=True)
    income_tax = fields.Monetary(
        string="Tax Withheld", compute='_calculate_all_rule_amounts', store=True)
    reimbursement = fields.Monetary(
        string="Reimbursement", compute='_calculate_all_rule_amounts', store=True)
    house_rent_allowance = fields.Monetary(
        string="Housing Allowance", compute='_calculate_all_rule_amounts', store=True)
    dearness_allowance = fields.Monetary(
        string="Dearness Allowance", compute='_calculate_all_rule_amounts', store=True)
    travel_allowance = fields.Monetary(
        string="Travel Allowance", compute='_calculate_all_rule_amounts', store=True)
    medical_allowance = fields.Monetary(
        string="Medical Allowance", compute='_calculate_all_rule_amounts', store=True)
    position_allowance = fields.Monetary(
        string="Position Allowance", compute='_calculate_all_rule_amounts', store=True)
    meal_allowance = fields.Monetary(
        string="Meal Allowance", compute='_calculate_all_rule_amounts', store=True)
    transport_home_allowance = fields.Monetary(
        string="Taxable Transport Allowance", compute='_calculate_all_rule_amounts', store=True)
    transport_work_allowance = fields.Monetary(
        string="Transport Work Allowance", compute='_calculate_all_rule_amounts', store=True)
    fuel_allowance = fields.Monetary(
        string="Fuel Allowance", compute='_calculate_all_rule_amounts', store=True)
    cash_indemnity_allowance = fields.Monetary(
        string="Cash Indemnity Allowance", compute='_calculate_all_rule_amounts', store=True)
    cash_indemnity_deduction = fields.Monetary(
        string="Cash Indemnity Deduction", compute='_calculate_all_rule_amounts', store=True)
    cash_indemnity_reward = fields.Monetary(
        string="Cash Indemnity Reward", compute='_calculate_all_rule_amounts', store=True)
    professional_allowance = fields.Monetary(
        string="Professional Allowance", compute='_calculate_all_rule_amounts', store=True)
    other_allowance = fields.Monetary(
        string="Other Allowance", compute='_calculate_all_rule_amounts', store=True)
    agreed_deduction = fields.Monetary(
        string="Saving Deduction", compute='_calculate_all_rule_amounts', store=True)
    social_commite = fields.Monetary(
        string="Social Committee", compute='_calculate_all_rule_amounts', store=True)
    none_taxiable_transport_allowance = fields.Monetary(
        string="Transport Allowance", compute='_calculate_all_rule_amounts',
        store=True)
    over_time = fields.Monetary(
        string="Over Time", compute='_calculate_all_rule_amounts', store=True)
    loan = fields.Monetary(
        string="Company Loan Repayment", compute='_calculate_all_rule_amounts', store=True)
    lunch = fields.Monetary(
        string="Cafteria Deduction", compute='_calculate_all_rule_amounts', store=True)
    taxable_salary = fields.Monetary(
        string="Total Taxable Earning", compute='_calculate_all_rule_amounts', store=True)
    pension_company = fields.Monetary(
        string="Pension Contribution 11%", compute='_calculate_all_rule_amounts', store=True)
    gross = fields.Monetary(
        string="Gross", compute='_calculate_all_rule_amounts', store=True)
    other_deduction = fields.Monetary(
        string="Other Deduction", compute='_calculate_all_rule_amounts', store=True)
    total_none_taxiable = fields.Monetary(
        string="Total Nontaxable Allowance", compute='_calculate_all_rule_amounts', store=True)
    marged_net = fields.Monetary(
        string="Total On Bank Letter", compute='_compute_total_on_bank_latter', store=True)

    total_ppension = fields.Monetary(
        string="PID", compute='_compute_total_pension', store=True)
    employee_tin = fields.Char(
        string="Employee TIN", related='employee_id.tin_no', store=True, readonly=True)

    employee_search_key = fields.Char(
        string="Search Key",
        compute='_compute_employee_search_key',
        store=True,
        readonly=True,
        help="Concatenation of employee name, employee ID, phone, and email for searching")

    @api.depends('employee_id', 'employee_id.name', 'employee_id.identification_id',
                 'employee_id.work_phone', 'employee_id.mobile_phone', 'employee_id.work_email')
    def _compute_employee_search_key(self):
        """Compute the employee search key by concatenating name, ID, phone, and email"""
        for record in self:
            search_parts = []

            # Employee name
            if record.employee_id and record.employee_id.name:
                search_parts.append(record.employee_id.name)

            # Employee ID number
            if record.employee_id and record.employee_id.identification_id:
                search_parts.append(record.employee_id.identification_id)

            # Phone (try work_phone first, then mobile_phone)
            if record.employee_id:
                phone = record.employee_id.work_phone or record.employee_id.mobile_phone or ''
                if phone:
                    search_parts.append(phone)

            # Email
            if record.employee_id and record.employee_id.work_email:
                search_parts.append(record.employee_id.work_email)

            record.employee_search_key = ' '.join(
                search_parts) if search_parts else ''

    @api.depends('pension', 'pension_company')
    def _compute_total_pension(self):
        for record in self:
            record.total_ppension = record.pension + record.pension_company

    @api.depends('employee_id', 'payslip_run_id', 'net_wage')
    def _compute_total_on_bank_latter(self):
        for record in self:
            record.marged_net = 0
            if record.employee_id.other_employee:
                other_net = self.env['hr.payslip'].search([
                    ('employee_id', '=', record.employee_id.other_employee.id),
                    ('payslip_run_id', '=', record.payslip_run_id.id),
                ])
                net = sum(other_net.line_ids.filtered(
                    lambda l: l.code == 'NET').mapped('total'))

                if other_net:
                    record.marged_net = net

    employee_bank_id = fields.Many2one(
        'res.bank',
        string="Bank",
        related='employee_id.bank_account_id.bank_id',
        store=True,
        readonly=True
    )

    calculate_active_rate = fields.Float(
        string="active rate ",
        compute='_calculate_active_rate',
    )

    old_contract_id = fields.Many2one(
        'hr.contract',
        string="Old Contract",
        compute="_compute_old_contract_id",
    )
    old_active_rate = fields.Float(
        string="Old Active Rate ",
        compute='_calculate_old_active_rate',
    )

    @api.depends('employee_id', 'date_from', 'date_to', 'contract_id')
    def _compute_old_contract_id(self):
        for record in self:
            old_contract = self.env['hr.contract'].search([
                ('employee_id', '=', record.employee_id.id),
                ('id', '!=', record.contract_id.id),
            ], order='date_end desc', limit=1)
            record.old_contract_id = old_contract if old_contract else False

    @api.depends("department_id")
    def compute_employee_core_department(self):
        for record in self:
            if record.department_id:
                record.core_department = record.department_id.cost_center
            else:
                record.core_department = ''

    def _calculate_old_active_rate(self):
        for record in self:
            rate = 0.0
            if record.old_contract_id and record.date_from and record.date_to:
                # contract dates
                start_date = record.old_contract_id.date_start
                end_date = record.old_contract_id.date_end or record.date_to

                # period dates
                period_start = record.date_from
                period_end = record.date_to

                # find overlap between contract and payslip period
                overlap_start = max(start_date, period_start)
                overlap_end = min(end_date, period_end)

                if overlap_start <= overlap_end:
                    total_days = (period_end - period_start).days + 1
                    active_days = (overlap_end - overlap_start).days + 1
                    rate = active_days / total_days if total_days > 0 else 0.0

            record.old_active_rate = rate

    @api.depends('employee_id', 'date_from', 'date_to', 'contract_id.date_start', 'contract_id.date_end')
    def _calculate_active_rate(self):
        for record in self:
            rate = 0.0
            if record.contract_id and record.date_from and record.date_to:
                # contract dates
                start_date = record.contract_id.date_start
                end_date = record.contract_id.date_end or record.date_to

                # period dates
                period_start = record.date_from
                period_end = record.date_to

                # find overlap between contract and payslip period
                overlap_start = max(start_date, period_start)
                overlap_end = min(end_date, period_end)

                if overlap_start <= overlap_end:
                    total_days = (period_end - period_start).days + 1
                    active_days = (overlap_end - overlap_start).days + 1
                    rate = active_days / total_days if total_days > 0 else 0.0

            record.calculate_active_rate = rate

    @api.depends('line_ids.code', 'line_ids.total')
    def _calculate_all_rule_amounts(self):
        target_rule_codes = [
            'ATTACH_SALARY', 'ASSIG_SALARY', 'CHILD_SUPPORT', 'DEDUCTION', 'PENSION', 'INTAX', 'REIMBURSEMENT', 'SOCC', 'OT100', 'LO', "TAXSAL", 'LUNCHDED', "OTHDED", "NET",
            'HRA', 'DA', 'TRA', 'MEA', 'MEDA', 'POSA', 'THA', 'TWA', 'FUEL', 'CIA', 'CID', 'CIR', 'PROA', 'OTHA', 'AGREEDDED', 'TNONTAX', "GROSS ", 'PENSION11', "TOTALNONTAX"
        ]

        for payslip in self:
            rule_amounts = {
                line.code: line.total
                for line in payslip.line_ids
                if line.code in target_rule_codes
            }
            payslip.attachment_salary = rule_amounts.get('ATTACH_SALARY', 0.0)
            payslip.assignment_salary = rule_amounts.get('ASSIG_SALARY', 0.0)
            payslip.child_support = rule_amounts.get('CHILD_SUPPORT', 0.0)
            payslip.deduction = rule_amounts.get('DEDUCTION', 0.0)
            payslip.pension = rule_amounts.get('PENSION', 0.0)
            payslip.income_tax = rule_amounts.get('INTAX', 0.0)
            payslip.reimbursement = rule_amounts.get('REIMBURSEMENT', 0.0)
            payslip.house_rent_allowance = rule_amounts.get('HRA', 0.0)
            payslip.dearness_allowance = rule_amounts.get('DA', 0.0)
            payslip.travel_allowance = rule_amounts.get('TRA', 0.0)
            payslip.medical_allowance = rule_amounts.get('MEDA', 0.0)
            payslip.position_allowance = rule_amounts.get('POSA', 0.0)
            payslip.transport_home_allowance = rule_amounts.get('THA', 0.0)
            payslip.transport_work_allowance = rule_amounts.get('TWA', 0.0)
            payslip.meal_allowance = rule_amounts.get('MEA', 0.0)
            payslip.fuel_allowance = rule_amounts.get('FUEL', 0.0)
            payslip.cash_indemnity_allowance = rule_amounts.get('CIA', 0.0)
            payslip.cash_indemnity_deduction = rule_amounts.get('CID', 0.0)
            payslip.cash_indemnity_reward = rule_amounts.get('CIR', 0.0)
            payslip.professional_allowance = rule_amounts.get('PROA', 0.0)
            payslip.other_allowance = rule_amounts.get('OTHA', 0.0)
            payslip.agreed_deduction = rule_amounts.get('AGREEDDED', 0.0)
            payslip.none_taxiable_transport_allowance = rule_amounts.get(
                'TNONTAX', 0.0)
            payslip.social_commite = rule_amounts.get(
                'SOCC', 0.0)
            payslip.over_time = rule_amounts.get('OT100', 0.0)
            payslip.loan = rule_amounts.get('LO', 0.0)
            payslip.lunch = rule_amounts.get('LUNCHDED', 0.0)
            payslip.taxable_salary = rule_amounts.get('TAXSAL', 0.0)
            payslip.pension_company = rule_amounts.get('PENSION11', 0.0)
            payslip.gross = rule_amounts.get('GROSS', 0.0)
            payslip.other_deduction = rule_amounts.get('OTHDED', 0.0)
            payslip.total_none_taxiable = rule_amounts.get('TOTALNONTAX', 0.0)
            payslip.net_wage = rule_amounts.get('NET', 0.0)
