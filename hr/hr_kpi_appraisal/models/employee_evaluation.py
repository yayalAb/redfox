# employee_kpi_appraisal/models/employee_evaluation.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date


class EmployeeEvaluation(models.Model):
    _name = 'employee.evaluation'
    _description = 'Employee Performance Evaluation'

    def _get_default_period_type(self):
        return self.env['ir.config_parameter'].sudo().get_param('hr_appraisal.period_type', default='year')

    name = fields.Char(string="Evaluation Reference",
                       compute='_compute_name', store=True, readonly=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', string='Department',
                                    related='employee_id.department_id', store=True, readonly=True)
    job_id = fields.Many2one(
        'hr.job', string='Job Position', related='employee_id.job_id', readonly=True)
    manager_id = fields.Many2one(
        'hr.employee', string='Manager', related='employee_id.parent_id', readonly=True)
    date_appraisal = fields.Date(
        string='Next Appraisal Date', default=fields.Date.context_today)
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'),
                             ('done', 'Done')], string='Status', default='draft')

    line_ids = fields.One2many(
        'employee.evaluation.line',
        'evaluation_id',
        string='KPIs for Evaluation'
    )

    # --- UPDATED LOGIC ---
    total_kpi_weight = fields.Float(
        string="Total KPI Weight",
        compute='_compute_total_kpi_weight',
        store=True,
        help="This is the sum of the weights of all KPIs included in this evaluation."
    )

    final_score = fields.Float(
        string="Final Score",
        compute='_compute_final_score',
        store=True,
        help="The total weighted score for this evaluation, out of 100."
    )

    period_id = fields.Many2one('appraisal.period', string='Period', required=True)
    period_type = fields.Selection(
        selection=[
            ('quarter', 'Quarter'),
            ('half', 'Semi-Annual'),
            ('year', 'Annual'),
            ('custom', 'Custom')
        ],
        string="Period Type",
        default=_get_default_period_type
    )
    appraisal_start_date = fields.Date(related='period_id.date_start', string='Appraisal Start Date')
    appraisal_end_date = fields.Date(related='period_id.date_end', string='Appraisal End Date')

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._generate_kpis()
        return record

    @api.onchange('employee_id')
    def _onchange_employee_id_generate_kpis(self):
        self._generate_kpis()



    
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



    @api.depends('line_ids.weighted_score')
    def _compute_final_score(self):
        """Calculates the final score by summing the weighted scores of all lines."""
        for evaluation in self:
            evaluation.final_score = sum(
                evaluation.line_ids.mapped('weighted_score'))

    @api.depends('line_ids.weight')
    def _compute_total_kpi_weight(self):
        """Calculates total weight from the evaluation lines."""
        for evaluation in self:
            evaluation.total_kpi_weight = sum(
                evaluation.line_ids.mapped('weight'))


    @api.depends('employee_id')
    def _compute_name(self):
        for rec in self:
            if rec.employee_id:
                rec.name = f"Evaluation for {rec.employee_id.name}"
            else:
                rec.name = "New Evaluation"


    def _generate_kpis(self):
        for rec in self:
            rec.line_ids = [(5, 0, 0)]

            if not rec.employee_id:
                continue

            kpi_model = rec.env['appraisal.kpi']

            general_kpis = kpi_model.search([
                ('department_id', '=', False),
                ('employee_id', '=', False)
            ])

            department_kpis = kpi_model.search([
                ('department_id', '=', rec.department_id.id),
                ('employee_id', '=', False)
            ])

            employee_kpis = kpi_model.search([
                ('department_id', '=', rec.department_id.id),
                ('employee_id', '=', rec.employee_id.id)
            ])

            all_kpis = general_kpis | department_kpis | employee_kpis

            lines_to_create = []
            for kpi in all_kpis:
                calculated_score = 0.0

                if rec.employee_id.user_id:
                    tasks = rec.env['project.task'].search([
                        ('user_ids', '=', rec.employee_id.user_id.id),
                        ('kpi_id', '=', kpi.id),
                        ('task_result', '!=', 0),
                    ])
                    if tasks:
                        results = tasks.mapped('task_result')
                        calculated_score = sum(results) / len(results)

                lines_to_create.append((0, 0, {
                    'kpi_id': kpi.id,
                    'evaluation_result': calculated_score,
                }))

            rec.line_ids = lines_to_create