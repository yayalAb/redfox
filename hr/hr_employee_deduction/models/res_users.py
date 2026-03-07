from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    can_submit_deduction = fields.Boolean(
        string="Submit Deductions",
        compute="_compute_can_submit_deduction",
        inverse="_inverse_can_submit_deduction"
    )

    can_approve_deduction = fields.Boolean(
        string="Approve Deductions",
        compute="_compute_can_approve_deduction",
        inverse="_inverse_can_approve_deduction"
    )

    def _compute_can_submit_deduction(self):
        user_group = self.env.ref('hr_employee_deduction.group_employee_deduction_user')
        for user in self:
            user.can_submit_deduction = user_group in user.groups_id

    def _inverse_can_submit_deduction(self):
        user_group = self.env.ref('hr_employee_deduction.group_employee_deduction_user')
        for user in self:
            if user.can_submit_deduction:
                user.groups_id |= user_group
            else:
                user.groups_id -= user_group

    def _compute_can_approve_deduction(self):
        manager_group = self.env.ref('hr_employee_deduction.group_employee_deduction_manager')
        for user in self:
            user.can_approve_deduction = manager_group in user.groups_id

    def _inverse_can_approve_deduction(self):
        manager_group = self.env.ref('hr_employee_deduction.group_employee_deduction_manager')
        for user in self:
            if user.can_approve_deduction:
                user.groups_id |= manager_group
            else:
                user.groups_id -= manager_group
