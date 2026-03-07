from odoo import models, fields

class HrDegree(models.Model):
    _name = 'hr.educational.status'
    name = fields.Char(required=True)