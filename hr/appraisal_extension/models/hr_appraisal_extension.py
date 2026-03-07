from odoo import models, fields, api, _
import json
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date
import logging

_logger = logging.getLogger(__name__)

try:
    from lxml import html
except ImportError:
    _logger.warning(
        "The lxml library is not installed. HTML parsing will not work.")
    html = None


class HrAppraisal(models.Model):
    _inherit = 'hr.appraisal'

    # REMOVE any _sql_constraints you added for this, as they are not sufficient.
    # The @api.constrains below is the correct implementation for this logic.

    def _get_default_period_type(self):
        return self.env['ir.config_parameter'].sudo().get_param('hr_appraisal.period_type')

    # ... (all your other fields remain the same) ...
    appraisal_template_domain = fields.Char(
        compute='_compute_appraisal_template_domain', store=False)
    final_rating = fields.Char(
        string="Final Rating", readonly=True, tracking=True)
    final_score = fields.Float(readonly=True)
    period_id = fields.Many2one('appraisal.period', string='Period', required=True)
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
    appraisal_start_date = fields.Date(related='period_id.date_start', string='Appraisal Start Date')
    appraisal_end_date = fields.Date(related='period_id.date_end', string='Appraisal End Date')


    @api.constrains('employee_id', 'period_id')
    def _check_unique_appraisal_period(self):
        """
        Ensures that an employee has only one appraisal for a specific appraisal period.
        This logic remains correct and does not need to be changed.
        """
        for record in self:
            if record.employee_id and record.period_id:
                domain = [
                    ('id', '!=', record.id),
                    ('employee_id', '=', record.employee_id.id),
                    ('period_id', '=', record.period_id.id),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_(
                        "An appraisal for employee '%(employee)s' for the period '%(period)s' already exists."
                    ) % {
                        'employee': record.employee_id.name,
                        'period': record.period_id.name,
                    })


    @api.depends('job_id', 'department_id')
    def _compute_appraisal_template_domain(self):
        for appraisal in self:
            if appraisal.job_id:
                domain = [('job_id', '=', appraisal.job_id.id)]
            elif appraisal.department_id:
                domain = [('department_id', '=', appraisal.department_id.id)]
            else:
                domain = ['&', ('job_id', '=', False),
                          ('department_id', '=', False)]
            appraisal.appraisal_template_domain = json.dumps(domain)

    @api.onchange('department_id', 'job_id')
    def _onchange_appraisal_template_id(self):
        self.appraisal_template_id = False

    def write(self, vals):
        res = super().write(vals)
        if 'manager_feedback' in vals:
            self.action_calculate_final_rating()
        return res

    def action_calculate_final_rating(self):
        """
        Parses the manager_feedback HTML, calculates the average score from
        star ratings, finds the corresponding evaluation scale, and sets it.
        """
        if html is None:
            raise UserError(
                _("The lxml library is not installed on the server, which is required for this feature."))

        for appraisal in self:
            html_content = appraisal.manager_feedback
            if not html_content:
                appraisal.final_rating = "N/A - No feedback provided."
                appraisal.final_score = 0
                continue

            doc = html.fromstring(html_content)
            kpi_containers = doc.xpath(
                '//table[contains(@class, "o_table")]/tbody/tr')

            if not kpi_containers:
                appraisal.final_rating = "N/A - No KPI table found in feedback."
                appraisal.final_score = 0
                continue

            kpi_scores = []
            for container in kpi_containers:
                filled_stars = container.xpath(
                    './/i[contains(@class, "fa-star") and not(contains(@class, "fa-star-o"))]')
                total_stars = container.xpath(
                    './/i[contains(@class, "fa-star") or contains(@class, "fa-star-o")]')

                if total_stars:
                    rating_value = len(filled_stars)
                    rating_max = len(total_stars)
                    if rating_max > 0:
                        score = (rating_value / rating_max) * 100
                        kpi_scores.append(score)

            if not kpi_scores:
                appraisal.final_rating = "N/A - No KPIs found."
                appraisal.final_score = 0
                continue

            average_score = sum(kpi_scores) / len(kpi_scores)
            appraisal.final_score = average_score

            EvaluationScale = self.env['hr.appraisal.note']
            matching_scale = EvaluationScale.search([
                ('lower_bound', '<=', average_score),
                ('upper_bound', '>=', average_score),
                ('company_id', '=', appraisal.company_id.id)
            ], limit=1)

            if matching_scale:
                appraisal.final_rating = f"{matching_scale.name} | Score {average_score:.2f}%"
            else:
                appraisal.final_rating = f"Score {average_score:.2f}% (No matching scale)"
