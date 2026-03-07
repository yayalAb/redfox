from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from datetime import date


class InsuranceRenewalHistory(models.Model):
    _name = 'insurance.renewal.history'
    insurance_id = fields.Many2one(
        'employee.insurance.coverage', string="Insurance")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    total_annual_premium = fields.Float(string="Total Annual Premium")
    status = fields.Selection(
        selection=[
            ('original', "Original"),
            ('new', "New"),
        ],
        string="Status",
        default='new')

    @api.constrains('registered_date', 'expire_date')
    def _validate_schedule(self):
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError(
                    _("start date must not be greater than end date"))

    def renew_project(self):
        for rec in self:
            rec.insurance_id.write({
                'from_date': rec.start_date,
                'date_to': rec.end_date,
                'last_renewed_date': date.today(),
                'total_annual_premium': rec.total_annual_premium
            })
