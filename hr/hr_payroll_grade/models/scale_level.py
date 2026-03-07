from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ScaleLevel(models.Model):
    _name = 'scale.level'
    _description = 'Scale Level'

    name = fields.Char(string='Level', required=True)  # e.g. A, B, C
    salary_grade_value_id = fields.Many2one(
        'salary.grade.value', string='Salary Grade Value',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
