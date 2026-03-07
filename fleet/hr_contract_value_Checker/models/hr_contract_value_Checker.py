from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.constrains('final_yearly_costs', 'monthly_yearly_costs')
    def _check_positive_costs(self):
        for contract in self:
            if contract.final_yearly_costs < 0:
                raise ValidationError(_("Yearly Cost must be a positive value."))
            if contract.monthly_yearly_costs < 0:
                raise ValidationError(_("Monthly Cost must be a positive value."))