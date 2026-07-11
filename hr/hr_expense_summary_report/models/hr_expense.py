from odoo import models, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    def action_print_payment_request_summary(self):
        if not self:
            raise UserError(_("Please select at least one expense."))
        return self.env.ref(
            'hr_expense_summary_report.action_report_payment_request_summary'
        ).report_action(self)
