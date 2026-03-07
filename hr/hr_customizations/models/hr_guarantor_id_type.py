from odoo import models, fields

class HrGuarantorIdType(models.Model):
    _name = 'hr.guarantor.id.type'
    _description = 'Guarantor ID Type'
    _order = 'name'

    name = fields.Char(string='ID Type', required=True, translate=True)