from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SalaryGrade(models.Model):
    _name = 'salary.grade'
    _description = 'Salary Grade'

    name = fields.Char(string='Name')

    salary_grade_value_id = fields.Many2one(
        'salary.grade.value', string='Salary Grade Value',
        required=True,
        help="The Salary Grade Value this record applies to"
    )

    scale_level_id = fields.Many2one(
        'scale.level', string='Scale Level',
        required=True,
        help="Only scales for the selected Salary Grade Value"
    )
    position_id = fields.Many2one(
        'hr.job',
        string='Position'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id
    )

    # Company currency default:
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
    )

    # Base salary on contract is often "wage"
    wage = fields.Monetary(string='Wage', currency_field='currency_id')

    # The same allowance fields you have on hr.contract:
    house_rent_allowance = fields.Monetary(
        string='House Rent Allowance',   currency_field='currency_id')
    dearness_allowance = fields.Monetary(
        string='Dearness Allowance',    currency_field='currency_id')
    travel_allowance = fields.Monetary(
        string='Travel Allowance',      currency_field='currency_id')
    meal_allowance = fields.Monetary(
        string='Meal Allowance',        currency_field='currency_id')
    medical_allowance = fields.Monetary(
        string='Medical Allowance',     currency_field='currency_id')
    position_allowance = fields.Monetary(
        string='Position Allowance',    currency_field='currency_id')
    transport_home_allowance = fields.Monetary(
        string='Transport (Home)',      currency_field='currency_id')
    transport_work_allowance = fields.Monetary(
        string='Transport (Work)',      currency_field='currency_id')
    fuel_allowance = fields.Monetary(
        string='Fuel Allowance',        currency_field='currency_id')
    cash_indemnity_allowance = fields.Monetary(
        string='Cash Indemnity Allowance', currency_field='currency_id')
    professional_allowance = fields.Monetary(
        string='Professional Allowance', currency_field='currency_id')
    other_allowance = fields.Monetary(
        string='Other Allowance',       currency_field='currency_id')

    @api.constrains('salary_grade_value_id', 'scale_level_id')
    def _check_unique_salary_grade_combination(self):
        for rec in self:
            # The search domain must now also check the company
            existing = self.search([
                ('id', '!=', rec.id),
                ('salary_grade_value_id', '=', rec.salary_grade_value_id.id),
                ('scale_level_id', '=', rec.scale_level_id.id),
                # ('company_id', '=', rec.company_id.id) # ==> ADD THIS LINE <==
            ], limit=1)
            if existing:
                raise ValidationError(
                    f"A Salary Grade already exists for Grade '{rec.salary_grade_value_id.name}' "
                    f"and Scale Level '{rec.scale_level_id.name}'."
                )

    @api.constrains(
        'wage',
        'house_rent_allowance', 'dearness_allowance', 'travel_allowance',
        'meal_allowance', 'medical_allowance', 'position_allowance',
        'transport_home_allowance', 'transport_work_allowance',
        'fuel_allowance', 'cash_indemnity_allowance', 'other_allowance',
    )
    def _check_positive_values(self):
        for record in self:
            for fname in [
                'wage',
                'house_rent_allowance', 'dearness_allowance', 'travel_allowance',
                'meal_allowance', 'medical_allowance', 'position_allowance',
                'transport_home_allowance', 'transport_work_allowance',
                'fuel_allowance', 'cash_indemnity_allowance', 'other_allowance',
            ]:
                val = getattr(record, fname)
                if val and val < 0:
                    pretty = fname.replace('_', ' ').title()
                    raise ValidationError(
                        f'{pretty} must be a non‑negative number.')
