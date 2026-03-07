# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):

    _inherit = 'res.company'
    company_stamp = fields.Binary(
        string='Company Stamp',
        help='Company Stamp for the company, used in various reports and documents.')


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


class HrLoan(models.Model):
    _inherit = 'hr.loan'

    # Guarantor fields - Many2one to hr.employee
    guarantor_id = fields.Many2one(
        'hr.employee',
        string="Guarantor",
        help="Select the guarantor employee for this loan"
    )

    # Company representative fields - Many2one to hr.employee
    company_representative_id = fields.Many2one(
        'hr.employee',
        string="Company Representative",
        help="Select the company representative employee signing the loan agreement"
    )

    # Signature fields
    guarantor_signature = fields.Binary(
        string="Guarantor Signature",
        help="Signature of the guarantor"
    )
    company_representative_signature = fields.Binary(
        string="Company Representative Signature",
        help="Signature of the company representative"
    )
    employee_signature = fields.Binary(
        string="Employee Signature",
        help="Signature of the employee (debtor)"
    )

    @api.onchange('guarantor_id')
    def _onchange_guarantor_id(self):
        """Load guarantor signature from user if available"""
        if self.guarantor_id:
            # Try to get signature from user first
            if self.guarantor_id.user_id and hasattr(self.guarantor_id.user_id, 'sign_signature') and self.guarantor_id.user_id.sign_signature:
                self.guarantor_signature = self.guarantor_id.user_id.sign_signature
            # Fallback to employee signature if user signature not available
            elif hasattr(self.guarantor_id, 'emp_signature') and self.guarantor_id.emp_signature:
                self.guarantor_signature = self.guarantor_id.emp_signature

    @api.onchange('company_representative_id')
    def _onchange_company_representative_id(self):
        """Load company representative signature from user if available"""
        if self.company_representative_id:
            # Try to get signature from user first
            if self.company_representative_id.user_id and hasattr(self.company_representative_id.user_id, 'sign_signature') and self.company_representative_id.user_id.sign_signature:
                self.company_representative_signature = self.company_representative_id.user_id.sign_signature
            # Fallback to employee signature if user signature not available
            elif hasattr(self.company_representative_id, 'emp_signature') and self.company_representative_id.emp_signature:
                self.company_representative_signature = self.company_representative_id.emp_signature

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Load employee signature from user if available"""
        if self.employee_id:
            # Try to get signature from user first
            if self.employee_id.user_id and hasattr(self.employee_id.user_id, 'sign_signature') and self.employee_id.user_id.sign_signature:
                self.employee_signature = self.employee_id.user_id.sign_signature
            # Fallback to employee signature if user signature not available
            elif hasattr(self.employee_id, 'emp_signature') and self.employee_id.emp_signature:
                self.employee_signature = self.employee_id.emp_signature
