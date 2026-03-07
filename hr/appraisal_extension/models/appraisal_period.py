# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AppraisalPeriod(models.Model):
    _name = 'appraisal.period'
    _description = 'Appraisal Period'
    _order = 'date_start desc, name'


    def _get_default_period_type(self):
        return self.env['ir.config_parameter'].sudo().get_param('hr_appraisal.period_type')

    name = fields.Char(
        string="Period Name", 
        required=True,
        help="E.g., 'Q1 2024', 'Annual 2024', 'H1 2024'"
    )
    period_type = fields.Selection(
        selection=[
            ('quarter', 'Quarter'),
            ('half', 'Semi-Annual'),
            ('year', 'Annual'),
            ('custom', 'Custom')
        ],
        string="Period Type",
        required=True,
        default=_get_default_period_type
    )
    date_start = fields.Date(string="Start Date", required=True)
    date_end = fields.Date(string="End Date", required=True)
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        default=lambda self: self.env.company,
        required=True
    )

    _sql_constraints = [
        ('date_check', 'CHECK (date_start <= date_end)', 'The start date must be before or the same as the end date.'),
    ]

    @api.constrains('date_start', 'date_end', 'period_type', 'company_id')
    def _check_dates_overlap(self):
        """
        Prevents creating overlapping periods of the same type (except 'custom').
        """
        for period in self:
            # Custom periods are allowed to overlap
            if period.period_type == 'custom':
                continue

            # Search for other periods of the same type that overlap with this one
            domain = [
                ('id', '!=', period.id),
                ('company_id', '=', period.company_id.id),
                ('period_type', '=', period.period_type),
                ('date_start', '<=', period.date_end),
                ('date_end', '>=', period.date_start),
            ]

            overlapping_periods = self.search(domain, limit=1)
            if overlapping_periods:
                raise ValidationError(
                    _("The period '%(period_name)s' (%(start)s - %(end)s) overlaps with another period of the same type: '%(other_name)s'.") % {
                        'period_name': period.name,
                        'start': period.date_start,
                        'end': period.date_end,
                        'other_name': overlapping_periods.name,
                    }
                )