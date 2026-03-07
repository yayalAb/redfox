from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SalaryGradeValue(models.Model):
    _name = 'salary.grade.value'
    _description = 'Salary Grade Value'

    name = fields.Char(string='Grade', required=True)  # e.g. I, II, III

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
