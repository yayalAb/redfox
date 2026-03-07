from odoo import models, fields

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    employee_deduction_ids = fields.Many2many(
        'employee.deduction', 
        string='Employee Deductions', 
        readonly=True,
        relation='hr_payslip_employee_deduction_rel' 
    )

    def compute_sheet(self):
        res = super(HrPayslip, self).compute_sheet()

        for slip in self:
            slip.input_line_ids.filtered(lambda i: i.input_type_id.id in slip.employee_deduction_ids.deduction_type_id.input_type_id.ids).unlink()
            slip.employee_deduction_ids = [(5, 0, 0)]

            deductions = self.env['employee.deduction'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('date', '>=', slip.date_from),
                ('date', '<=', slip.date_to),
                ('state', '=', 'approved'),
            ])

            if deductions:
                slip.employee_deduction_ids = [(6, 0, deductions.ids)]

                for deduction in deductions:
                    self.env['hr.payslip.input'].create({
                        'payslip_id': slip.id,
                        'name': deduction.name,
                        'code': deduction.deduction_type_id.code,
                        'amount': deduction.amount,
                        'contract_id': slip.contract_id.id,
                        'input_type_id': deduction.deduction_type_id.input_type_id.id,
                    })
        return res

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for slip in self:
            if slip.employee_deduction_ids:
                slip.employee_deduction_ids.write({
                    'state': 'applied',
                    'payslip_id': slip.id
                })
        return res