# custom_payslip_reports/models/social_contribution_wizard.py
from odoo import models, fields, api
from odoo.exceptions import UserError


class SocialContributionWizard(models.TransientModel):
    _name = 'social.contribution.wizard'
    _description = 'Social Contribution Report Wizard'

    branch_id = fields.Many2one(
        'res.company',
        string='Branch',
        required=True
    )
    is_pension = fields.Boolean(
        string="Pension",
    )
    is_saving = fields.Boolean(
        string="Saving",
    )

    is_tax = fields.Boolean(
        string="Tax",
    )

    payslip_ids = fields.Many2many('hr.payslip')

    def print_report(self):
        self.ensure_one()

        branch_payslips = self.payslip_ids.filtered(
            lambda p: p.branch_id == self.branch_id)
        if not branch_payslips:
            raise UserError(
                f"No payslips found for the '{self.branch_id.name}' branch in your selection.")
        if self.is_pension:
            report_title = f"{self.branch_id.name} Pension Contribution"
            return self.env.ref('custom_payslip_reports.action_report_pension_contribution').with_context(report_title=report_title).report_action(branch_payslips)
        elif self.is_saving:
            report_title = f"{self.branch_id.name} Saving"
            return self.env.ref('custom_payslip_reports.action_report_saving_deduction').with_context(report_title=report_title).report_action(branch_payslips)
        elif self.is_tax:
            report_title = f"{self.branch_id.name} Tax Withheld"
            return self.env.ref('custom_payslip_reports.action_report_tax_withheld').with_context(report_title=report_title).report_action(branch_payslips)
        else:
            report_title = f"{self.branch_id.name} Social Contribution"
            return self.env.ref('custom_payslip_reports.action_report_social_contribution').with_context(report_title=report_title).report_action(branch_payslips)
