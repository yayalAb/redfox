from odoo import models, fields, api
from datetime import datetime, date

class EmployeeAppraisal(models.Model):
    _name = "employee.appraisal"
    _description = "Aggregated Employee Appraisal"


    def _get_default_period_type(self):
        return self.env['ir.config_parameter'].sudo().get_param('hr_appraisal.period_type', default='year')

    # --- Fields for selecting the period ---
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
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

    # --- Computed links to the source records ---
    employee_evaluation_id = fields.Many2one(
        "employee.evaluation",
        string="Source Evaluation",
        compute="_compute_source_records",
        store=True
    )
    appraisal_id = fields.Many2one(
        "hr.appraisal",
        string="Source Appraisal",
        compute="_compute_source_records",
        store=True
    )

    # --- Computed results based on the source records ---
    evaluation_result = fields.Float(
        compute="_compute_evaluation_result",
        string='Evaluation Result (70%)',
        store=True,
        readonly=True
    )
    appraisal_result = fields.Float(
        compute="_compute_appraisal_result",
        string='Appraisal Result (30%)',
        store=True,
        readonly=True
    )
    final_rating = fields.Float(
        string="Final Rating",
        compute='_compute_final_rating',
        store=True,
        readonly=True,
        help="The final rating for this appraisal, out of 100."
    )

    # --- Other related fields (can be useful for display) ---
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', store=True, readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', related='employee_id.job_id', readonly=True)
    manager_id = fields.Many2one('hr.employee', related='department_id.manager_id', string='Manager')
    appraisal_date = fields.Date(string='Appraisal Date', default=fields.Date.context_today)

    # --- COMPUTE METHODS ---

    @api.depends('employee_id', 'period_type', 'period_id')
    def _compute_source_records(self):
        """
        This single method computes BOTH the evaluation and appraisal links.
        It searches for matching records based on the selected period.
        """
        for rec in self:
            # Reset fields before attempting to search
            rec.appraisal_id = False
            rec.employee_evaluation_id = False
            
            # Continue only if we have the minimum required data
            if not all([rec.employee_id, rec.period_id, rec.period_type]):
                continue

            domain = [
                ('employee_id', '=', rec.employee_id.id),
                ('period_type', '=', rec.period_type),
                ('period_id', '=', rec.period_id.id),
            ]
            
            # --- Search for the matching records ---
            found_appraisal = self.env['hr.appraisal'].search(domain, limit=1)
            rec.appraisal_id = found_appraisal.id if found_appraisal else False
            
            found_evaluation = self.env['employee.evaluation'].search(domain, limit=1)
            rec.employee_evaluation_id = found_evaluation.id if found_evaluation else False

    @api.depends('employee_evaluation_id.final_score')
    def _compute_evaluation_result(self):
        """Calculates the weighted score from the employee evaluation."""
        for rec in self:
            if rec.employee_evaluation_id:
                # Corrected: use `rec` not `res`
                rec.evaluation_result = rec.employee_evaluation_id.final_score * 0.7
            else:
                rec.evaluation_result = 0.0

    @api.depends('appraisal_id.final_score')
    def _compute_appraisal_result(self):
        """Calculates the weighted score from the manager's appraisal."""
        for rec in self:
            if rec.appraisal_id:
                # Corrected: use `rec` not `res`
                rec.appraisal_result = rec.appraisal_id.final_score * 0.3
            else:
                rec.appraisal_result = 0.0

    @api.depends('evaluation_result', 'appraisal_result')
    def _compute_final_rating(self):
        """Sums the two weighted results to get the final score."""
        for rec in self:
            # No need for an if/else check, summing with 0.0 is safe
            final = rec.evaluation_result + rec.appraisal_result
            rec.final_rating = round(final, 2)