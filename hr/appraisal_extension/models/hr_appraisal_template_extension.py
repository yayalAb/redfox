from odoo import models, fields

class HrAppraisalTemplate(models.Model):
    _inherit = 'hr.appraisal.template'

    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one(
        'hr.job',
        string='Position',
        domain='[("department_id", "=", department_id)]'
    )
