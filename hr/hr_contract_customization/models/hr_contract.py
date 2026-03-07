from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    apply_cash_indemnity = fields.Boolean("Apply Cash Indemnity")
    cash_indemnity_start_date = fields.Date(string="Cash Indemnity Start Date")

    house_rent_allowance = fields.Monetary(help='House Rent Allowance')
    dearness_allowance = fields.Monetary(help='Dearness Allowance')
    travel_allowance = fields.Monetary()
    meal_allowance = fields.Monetary()
    medical_allowance = fields.Monetary()
    position_allowance = fields.Monetary()
    transport_home_allowance = fields.Monetary()
    transport_work_allowance = fields.Monetary()
    fuel_allowance = fields.Monetary()
    cash_indemnity_allowance = fields.Monetary()
    professional_allowance = fields.Monetary()
    other_allowance = fields.Monetary()

    @api.onchange('apply_cash_indemnity')
    def _onchange_cash_indemnity_allowance(self):
        for record in self:
            if not record.apply_cash_indemnity:
                record.cash_indemnity_allowance = 0
                record.cash_indemnity_start_date = False

    @api.constrains('cash_indemnity_start_date')
    def _check_cash_indemnity_start_date(self):
        for record in self:
            if record.apply_cash_indemnity and not record.cash_indemnity_start_date:
                raise ValidationError('Cash indemnity start date is required if cash indemnity applies.')

    @api.constrains('house_rent_allowance',
                    'dearness_allowance', 'travel_allowance', 'meal_allowance',
                    'medical_allowance', 'position_allowance', 'transport_home_allowance',
                    'transport_work_allowance', 'fuel_allowance', 'professional_allowance', 
                    'other_allowance', 'cash_indemnity_allowance'
                    )
    def _check_positive_values(self):
        for record in self:
            fields_to_check = [
                ('house_rent_allowance', record.house_rent_allowance),
                ('dearness_allowance', record.dearness_allowance),
                ('travel_allowance', record.travel_allowance),
                ('meal_allowance', record.meal_allowance),
                ('medical_allowance', record.medical_allowance),
                ('position_allowance', record.position_allowance),
                ('transport_home_allowance', record.transport_home_allowance),
                ('transport_work_allowance', record.transport_work_allowance),
                ('fuel_allowance', record.fuel_allowance),
                ('cash_indemnity_allowance', record.cash_indemnity_allowance),
                ('professional_allowance', record.professional_allowance),
                ('other_allowance', record.other_allowance),
            ]
            for field_name, value in fields_to_check:
                if value and value < 0:
                    raise ValidationError(
                        f'{field_name.replace("_", " ").title()} must be a non-negative number.')
