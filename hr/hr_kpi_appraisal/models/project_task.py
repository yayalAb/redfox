from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    kpi_id = fields.Many2one(
        'appraisal.kpi', 
        string="Associated KPI",
        help="The Key Performance Indicator that this task contributes to."
    )
    
    time_efficiency_score = fields.Float(
        string="Time Efficiency Score (%)",
        compute="_compute_task_result",
        store=True,
        help="Performance score based on allocated vs. spent time. Contributes 80% to the final result."
    )

    deadline_adherence_score = fields.Float(
        string="Deadline Score (%)",
        compute="_compute_task_result",
        store=True,
        help="Performance score based on meeting the task deadline. Contributes 20% to the final result."
    )

    task_result = fields.Float(
        string="Task Result (%)",
        help="The final performance score for this task's completion, from 0 to 100.",
        compute="_compute_task_result",
        store=True,
    )

    @api.depends('stage_id', 'stage_id.fold', 'allocated_hours', 'total_hours_spent', 'date_deadline', 'date_end')
    def _compute_task_result(self):
        for task in self:
            if not task.stage_id or not task.stage_id.fold:
                task.time_efficiency_score = 0
                task.deadline_adherence_score = 0
                task.task_result = 0
                continue

            time_score = 0.0
            spent_hours = task.total_hours_spent
            allocated_hours = task.allocated_hours

            if allocated_hours > 0:
                if spent_hours <= allocated_hours:
                    time_score = 100.0
                else:
                    calculated_score = (2 * allocated_hours - spent_hours) / allocated_hours * 100.0
                    time_score = max(0.0, calculated_score)
            elif allocated_hours == 0 and spent_hours == 0:
                time_score = 100.0
            else:
                time_score = 0.0
            
            task.time_efficiency_score = time_score

            deadline_score = 0.0
            if not task.date_deadline:
                deadline_score = 100.0
            elif task.date_end and task.date_deadline:
                if task.date_end.date() <= task.date_deadline.date():
                    deadline_score = 100.0
            
            task.deadline_adherence_score = deadline_score

            final_result = (time_score * 0.8) + (deadline_score * 0.2)
            task.task_result = final_result