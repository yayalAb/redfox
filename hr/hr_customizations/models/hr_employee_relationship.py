from odoo import api, fields, models

class HrEmployeeRelationship(models.Model):
    _name = 'hr.employee.relationship'
    _description = 'Emergency Contact Relationship'

    name = fields.Char(
        string='Relationship',
        required=True,
        help="E.g. Spouse, Parent, Friend, etc."
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Inactive relationships will be hidden from the dropdown."
    )