from odoo import models, fields

class HrFieldOfStudy(models.Model):
    _name = 'hr.field.study'
    _description = 'Field of Study'
    name = fields.Char(string='Field of Study', required=True, translate=True)