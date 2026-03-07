from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class HrleaveRequest(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('request_date_from', 'request_date_to', 'holiday_status_id', 'number_of_days')
    def _check_leave_balance(self):
        for record in self:
            if record.holiday_status_id.requires_allocation == 'no':
                leaves = record.env['hr.leave'].search(
                    [('id', '!=', record.id), ('employee_id', '=', record.employee_id.id), ('state', 'in', ['confirm', 'validate1', 'validate']), ('holiday_status_id', '=', record.holiday_status_id.id)])
                
                days_taken = sum(leaves.mapped('number_of_days'))
                new_total_days = days_taken + record.number_of_days
                max_balance = record.holiday_status_id.max_balance
                if new_total_days > max_balance and record.holiday_status_id.requires_allocation == 'yes':
                    raise ValidationError(
                        f"This leave request exceeds the maximum balance of {max_balance} days "
                        f"for the '{record.holiday_status_id.name}' leave type. "
                        f"You have already taken {days_taken} day(s)."
                    )
                    
    @api.constrains('holiday_status_id', 'employee_id', 'state')
    def _check_probation_period(self):
        
        for record in self:
            
            if record.state not in ['confirm', 'validate'] or not record.holiday_status_id.requires_probation:
                continue

            if not record.employee_id:
                raise ValidationError(_("An employee must be selected."))

            contract = self.env['hr.contract'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)

            if not contract or not contract.date_start:
                raise ValidationError(_(
                    "Probation period could not be checked: The employee '%s' does not have an active contract with a start date.",
                    record.employee_id.name
                ))
            manager_of_count = self.env['hr.employee'].search_count([('parent_id', '=', record.employee_id.id)])
            is_manager = manager_of_count > 0
            probation_months = 3 if is_manager else 2
            
            contract_start_date = contract.date_start
            probation_end_date = contract_start_date + relativedelta(months=probation_months)
            
            request_date = record.request_date_from or fields.Date.context_today(record)

            if request_date < probation_end_date:
                raise ValidationError(
                    _("This leave type cannot be requested. %s has not completed the %s-month probation period, which ends on %s.") % 
                    (record.employee_id.name, probation_months, fields.Date.to_string(probation_end_date))
                )
