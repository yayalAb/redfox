# employee_kpi_appraisal/models/employee_evaluation_line.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EmployeeEvaluationLine(models.Model):
    _name = 'employee.evaluation.line'
    _description = 'Employee Evaluation Line'

    evaluation_id = fields.Many2one('employee.evaluation', string='Evaluation', required=True, ondelete='cascade')
    kpi_id = fields.Many2one('appraisal.kpi', string='KPI', required=True)

    # Related fields from the KPI for easy display
    kpi_type = fields.Char(related='kpi_id.kpi_type', string='KPI Type', readonly=True, store=True)
    weight = fields.Float(related='kpi_id.weight', string='Weight (%)', store=True, readonly=False)

    
    # --- THIS IS THE NEW FIELD FOR THE RESULT ---
    evaluation_result = fields.Float(
        string="Evaluation_result", 
        default=0.0
    )

    # --- NEW: This field calculates the line's contribution to the final score ---
    weighted_score = fields.Float(
        string="Weighted Score",
        compute='_compute_weighted_score',
        store=True,
        help="The final score contribution of this line. (Score / 5) * Normalized Weight."
    )


    @api.depends('evaluation_result', 'weight')
    def _compute_weighted_score(self):
        """
        Calculates the score for this line based on its normalized weight.
        The score is scaled from 0-5 to a 0-100 scale.
        """
        for line in self:
            performance_ratio = line.weight / 100
            line.weighted_score = (performance_ratio * line.evaluation_result)