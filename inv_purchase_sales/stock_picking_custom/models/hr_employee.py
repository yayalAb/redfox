from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    emp_signature = fields.Binary('Employee Signature')