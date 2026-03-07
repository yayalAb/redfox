from odoo import models, fields, api


class PayslipWithCustomColumns(models.Model):
    _inherit = 'hr.payslip'

    # branch_id = fields.Many2one(
    #     string="Branch", related="employee_id.brach_id", store=True, readonly=True)
    # branch_name = fields.Char(related='employee_id.brach_id.name', string="Branch", store=True)

    basic_wage = fields.Monetary(
        string="Basic Salary", store=True)
    gross_wage = fields.Monetary(
        string="Gross Earning", store=True)
    net_wage = fields.Monetary(
        string="Net Pay", store=True)
    sequence_no = fields.Integer(
        string='S.No.')

    # employee_id_no = fields.Char(
    #     string="Employee ID", related='employee_id.identification_id', store=True, readonly=True)

    # hr_contract_start = fields.Date(
    #     string="Start Date", related='contract_id.date_start', store=True, readonly=True)
    # hr_contract_end = fields.Date(
    #     string="End Date", related='contract_id.date_end', store=True, readonly=True)

    pension = fields.Monetary(
        string="Pension Contribution 7%", compute='_calculate_all_rule_amounts', store=True)
    income_tax = fields.Monetary(
        string="Tax Whithheld", compute='_calculate_all_rule_amounts', store=True)
    house_rent_allowance = fields.Monetary(
        string="Housing Allowance", compute='_calculate_all_rule_amounts', store=True)
    position_allowance = fields.Monetary(
        string="Position Allowance", compute='_calculate_all_rule_amounts', store=True)
    transport_home_allowance = fields.Monetary(
        string="Taxable Transport Allowance", compute='_calculate_all_rule_amounts', store=True)
    professional_allowance = fields.Monetary(
        string="Professional Allowance", compute='_calculate_all_rule_amounts', store=True)
    other_allowance = fields.Monetary(
        string="Other Allowance", compute='_calculate_all_rule_amounts', store=True)
    agreed_deduction = fields.Monetary(
        string="Saving Deduction", compute='_calculate_all_rule_amounts', store=True)
    social_commite = fields.Monetary(
        string="Social Committee", compute='_calculate_all_rule_amounts', store=True)
    none_taxiable_transport_allowance = fields.Monetary(
        string="Non Taxable Transport Allowance", compute='_calculate_all_rule_amounts',
        store=True)
    over_time = fields.Monetary(
        string="Over Time", compute='_calculate_all_rule_amounts', store=True)
    loan = fields.Monetary(
        string="Company Loan Repayment", compute='_calculate_all_rule_amounts', store=True)
    lunch = fields.Monetary(
        string="Cafteria Deduction", compute='_calculate_all_rule_amounts', store=True)
    taxable_salary = fields.Monetary(
        string="Total Taxable", compute='_calculate_all_rule_amounts', store=True)
    pension_company = fields.Monetary(
        string="Pension Contribution 11%", compute='_calculate_all_rule_amounts', store=True)
    other_deduction = fields.Monetary(
        string="Other Deduction", compute='_calculate_all_rule_amounts', store=True)
    total_none_taxiable = fields.Monetary(
        string="Total Nontaxable Allowance", compute='_calculate_all_rule_amounts', store=True)
    deduction = fields.Monetary(
        string="Total Deduction", compute='_calculate_all_rule_amounts', store=True)
    employee_tin = fields.Char(
        string="Employee TIN", related='employee_id.tin_no', store=True,
        help="Related to the TIN/VAT field on the employee record.")
    other_taxable_benefits = fields.Monetary(
        string="Other Taxable Benefit", compute='_calculate_all_rule_amounts', store=True,
        help="Sum of Professional, Position, and Housing Allowances.")
    cost_sharing = fields.Monetary(
        string="Cost Sharing", compute='_calculate_all_rule_amounts', store=True,
        help="Corresponds to a salary rule with the code 'COSTSH'.")
    job_position = fields.Char(
        string="Position", related='employee_id.job_id.name', store=False,
        help="Related to the Job Position on the employee record.")

    total_pension_contribution = fields.Monetary(
        string="PID", compute='compute_total_pension_contribution', store=True,
        help="Sum of Employee and Company Pension Contributions.")

    @api.depends('pension', 'pension_company')
    def compute_total_pension_contribution(self):
        for record in self:
            record.total_pension_contribution = record.pension + record.pension_company

    @api.depends('line_ids.total')
    def _calculate_all_rule_amounts(self):
        for slip in self:
            slip.basic_wage = sum(slip.line_ids.filtered(
                lambda r: r.code == 'BASIC').mapped('total'))
            slip.gross_wage = sum(slip.line_ids.filtered(
                lambda r: r.code == 'GROSS').mapped('total'))
            slip.net_wage = sum(slip.line_ids.filtered(
                lambda r: r.code == 'NET').mapped('total'))
            slip.pension = sum(slip.line_ids.filtered(
                lambda r: r.code == 'PENSION').mapped('total'))
            slip.income_tax = sum(slip.line_ids.filtered(
                lambda r: r.code == 'INTAX').mapped('total'))
            slip.house_rent_allowance = sum(slip.line_ids.filtered(
                lambda r: r.code == 'HRA').mapped('total'))
            slip.position_allowance = sum(slip.line_ids.filtered(
                lambda r: r.code == 'POSA').mapped('total'))
            slip.transport_home_allowance = sum(slip.line_ids.filtered(
                lambda r: r.code == 'THA').mapped('total'))
            slip.professional_allowance = sum(slip.line_ids.filtered(
                lambda r: r.code == 'PROA').mapped('total'))
            slip.other_allowance = sum(slip.line_ids.filtered(
                lambda r: r.code == 'OTHA').mapped('total'))
            slip.agreed_deduction = sum(slip.line_ids.filtered(
                lambda r: r.code == 'AGREEDDED').mapped('total'))
            slip.social_commite = sum(slip.line_ids.filtered(
                lambda r: r.code == 'SOCC').mapped('total'))
            slip.none_taxiable_transport_allowance = sum(
                slip.line_ids.filtered(lambda r: r.code == 'TNONTAX').mapped('total'))
            slip.over_time = sum(slip.line_ids.filtered(
                lambda r: r.code == 'OT100').mapped('total'))
            slip.loan = sum(slip.line_ids.filtered(
                lambda r: r.code == 'LO').mapped('total'))
            slip.lunch = sum(slip.line_ids.filtered(
                lambda r: r.code == 'LUNCHDED').mapped('total'))
            slip.taxable_salary = sum(slip.line_ids.filtered(
                lambda r: r.code == 'TAXSAL').mapped('total'))
            slip.pension_company = sum(slip.line_ids.filtered(
                lambda r: r.code == 'PENSION11').mapped('total'))
            slip.other_deduction = sum(slip.line_ids.filtered(
                lambda r: r.code == 'OTHDED').mapped('total'))
            slip.total_none_taxiable = sum(slip.line_ids.filtered(
                lambda r: r.code == 'TOTALNONTAX').mapped('total'))
            slip.deduction = sum(slip.line_ids.filtered(
                lambda r: r.code == 'DEDUCTION').mapped('total'))
            slip.other_taxable_benefits = slip.professional_allowance + \
                slip.position_allowance + slip.house_rent_allowance
            slip.cost_sharing = sum(slip.line_ids.filtered(
                lambda r: r.code == 'COSTSH').mapped('total'))

    @api.depends('name')
    def _compute_sequence_no(self):
        for index, record in enumerate(self.sorted(key=lambda r: r.employee_id.name), start=1):
            record.sequence_no = index

    def action_open_payslip_report_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payslip Reports',
            'res_model': 'payslip.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_payslip_ids': self.ids}
        }
