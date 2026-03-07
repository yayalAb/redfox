from odoo import models, fields, api

class Project(models.Model):
    _inherit = "project.project"

    project_result = fields.Float(
        string="Project Result (%)",
        help="The average performance score of all completed tasks directly displayed in this project.",
        compute="_compute_project_result",
        store=True, 
    )

    @api.depends('tasks.task_result', 'tasks.display_in_project', 'tasks.stage_id.fold')
    def _compute_project_result(self):
        for project in self:
            if not project.tasks:
                project.project_result = 0.0
                continue

            all_task_results = project.tasks.mapped('task_result')

            average_result = sum(all_task_results) / len(all_task_results)
            project.project_result = average_result