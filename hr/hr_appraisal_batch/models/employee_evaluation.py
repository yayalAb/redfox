from odoo import models,fields

class EmployeeEvaluation(models.Model):
    _inherit = "employee.evaluation"

    batch_id = fields.Many2one('evaluation.batch', String="Batch")