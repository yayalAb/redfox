# evaluation_batch.py
from odoo import models, fields, api

class EvaluationBatch(models.Model):
    _name = "evaluation.batch"
    _description = "Evaluation Batch"

    def _get_default_period_type(self):
        return self.env['ir.config_parameter'].sudo().get_param('hr_appraisal.period_type')

    name = fields.Char(string="Batch Name", required=True)
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
    start_date = fields.Date(related='period_id.date_start', string='Start Date', store=True)
    end_date = fields.Date(related='period_id.date_end', string='End Date', store=True)
    evaluation_line_ids = fields.One2many('employee.evaluation', 'batch_id', string="Evaluation Lines")

    # --- NEW FIELD AND METHOD DEFINITIONS ---

    evaluation_count = fields.Integer(
        string="Evaluation Count", 
        compute='_compute_evaluation_count'
    )

    @api.depends('evaluation_line_ids')
    def _compute_evaluation_count(self):
        """Calculates the number of evaluations linked to this batch."""
        for batch in self:
            batch.evaluation_count = len(batch.evaluation_line_ids)

    def action_view_evaluations(self):
        """
        This method is called when the 'Evaluations' stat button is clicked.
        It returns an action that opens a tree view of all evaluations
        linked to this batch.
        """
        self.ensure_one()
        return {
            'name': 'Evaluations',
            'type': 'ir.actions.act_window',
            'res_model': 'employee.evaluation',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.evaluation_line_ids.ids)],
            'context': {
                'default_batch_id': self.id,
                'default_period_id': self.period_id.id,
                'default_period_type': self.period_type,
            }
        }