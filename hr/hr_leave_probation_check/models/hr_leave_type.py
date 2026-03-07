from odoo import models, fields, api


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    max_balance = fields.Float(string='Maximum Balance')
    requires_probation = fields.Boolean(
        string="Requires Probation Period",
        help="If checked, an employee must have completed their probation period to request this type of time off."
    )