from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from datetime import date
class InsuranceCopyEmployee(models.TransientModel):
    _name = 'insurance.copy.employee'
    insurance_id = fields.Many2one('employee.insurance.coverage', string="Insurance")
    employee_ids = fields.Many2many('hr.employee', string="Employees", required=True)

    def on_save_employee_insurance_copy(self):
        for rec in self.employee_ids:
            print("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr: ",rec)

            insurance_line = [(0, 0, {
                'employee_id': rec.id,
                'insurance_coverage_id': line.insurance_coverage_id.id,
                'value': line.value,
                'coverage_type': line.coverage_type.id,
            }) for line in self.insurance_id.insurance_coverage_ids]

            self.env['employee.insurance.coverage'].create({
                'name': self.insurance_id.name,
                'employee_id': rec.id,
                'category_id': self.insurance_id.category_id.id,
                'provider_id': self.insurance_id.provider_id.id,
                'insurance_coverage_ids':insurance_line,
                'total_claim': self.insurance_id.total_claim,
                'from_date': self.insurance_id.from_date,
                'date_to': self.insurance_id.date_to,
                'total_annual_premium': self.insurance_id.total_annual_premium,
                'last_renewed_date': self.insurance_id.last_renewed_date,
                'status': self.insurance_id.status,
            })
