from odoo import models


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import SQL


class ResCompany(models.Model):

    _inherit = 'res.company'
    company_stamp = fields.Binary(
        string='Company Stamp',
        help='Company Stamp for the company, used in various reports and documents.')


class HrContractSalaryOffer(models.Model):
    _inherit = 'hr.contract.salary.offer'

    def action_send_by_email(self):
        action = super().action_send_by_email()
        custom_template_id = self.env.ref(
            'hr_offer.email_template_custom_applicant_offer').id
        action['context']['default_template_id'] = custom_template_id
        return action


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def get_salary_grade_info(self):
        """Helper method to safely get salary grade and scale level from contract"""
        self.ensure_one()
        contract = self.contract_id
        if not contract:
            return {'salary_grade': None, 'scale_level': None}

        salary_grade = None
        scale_level = None

        # Try relation fields first
        if hasattr(contract, 'salary_grade_value_id') and contract.salary_grade_value_id:
            salary_grade = contract.salary_grade_value_id.name
        elif hasattr(contract, 'salary_grade') and contract.salary_grade:
            salary_grade = contract.salary_grade
        elif hasattr(contract, 'job_grade') and contract.job_grade:
            salary_grade = contract.job_grade

        if hasattr(contract, 'scale_level_id') and contract.scale_level_id:
            scale_level = contract.scale_level_id.name
        elif hasattr(contract, 'scale_level') and contract.scale_level:
            scale_level = contract.scale_level

        return {
            'salary_grade': salary_grade,
            'scale_level': scale_level
        }


class HrContract(models.Model):
    _inherit = 'hr.contract'

    approval_status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('reviewed', 'Reviewed'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='Approval Status',
        default='draft',
        tracking=True,
    )
    reviewed_by_id = fields.Many2one(
        'res.users',
        string='Reviewed By',
    )
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
    )

    def action_set_to_draft(self):
        for record in self:
            record.approval_status = 'draft'
            record.reviewed_by_id = False
            record.approved_by_id = False

    def action_set_to_reviewed(self):
        for record in self:
            record.approval_status = 'reviewed'
            record.reviewed_by_id = self.env.user

    def action_set_to_approved(self):
        for record in self:
            record.approval_status = 'approved'
            record.approved_by_id = self.env.user
