from odoo import models, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):

        for payslip in self:

            contract = payslip.contract_id
            if not payslip.employee_id or not payslip.date_to or not contract or not contract.apply_cash_indemnity:
                continue

            start_date = contract.cash_indemnity_start_date
            end_date = payslip.date_to
            
            month_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

            allowance_amount = 0.0

            if month_diff <= 12:
                allowance_amount = 0.0
            else:
                if (month_diff - 12) % 3 == 0:
                    total_deduction = 0.0

                    total_deduction += contract.cash_indemnity_allowance

                    past_payslips = self.env['hr.payslip'].search([
                        ('employee_id', '=', payslip.employee_id.id),
                        ('date_to', '<', payslip.date_to),
                        ('state', 'in', ['done', 'paid']),
                    ], order='date_to desc', limit=2)
                    
                    for past_slip in past_payslips:
                        past_deduction_line = past_slip.line_ids.filtered(
                            lambda line: line.code == 'CIA'
                        )
                        if past_deduction_line:
                            total_deduction += past_deduction_line.total
                    
                    allowance_amount = total_deduction

                else:
                    allowance_amount = 0.0
            
            if allowance_amount > 0:
                cia_input = payslip.input_line_ids.filtered(
                    lambda l: l.code == 'CIR')
                if cia_input:
                    cia_input.amount = allowance_amount
                else:
                    payslip.input_line_ids = [(0, 0, {
                        'code': 'CIR',
                        'name': 'Cash Indemnity Reward',
                        'amount': allowance_amount,
                        'input_type_id': self.env.ref('hr_contract_customization.hr_payroll_input_CIR').id,
                    })]
        return super(HrPayslip, self).compute_sheet()