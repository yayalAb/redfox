# custom_payslip_reports/models/payslip_report_wizard.py
from odoo import models, fields


class PayslipReportWizard(models.TransientModel):
    _name = 'payslip.report.wizard'
    _description = 'Payslip Report Wizard'

    payslip_ids = fields.Many2many('hr.payslip', string='Payslips')

    def action_print_payroll_sheet(self):
        return self.env.ref('custom_payslip_reports.action_report_payroll_sheet').report_action(self.payslip_ids)

    def action_print_tax_withheld_report(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Branch',
            'res_model': 'social.contribution.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_ids': [(6, 0, self.payslip_ids.ids)],
                'default_is_tax': True,
            }}

        # return self.env.ref('custom_payslip_reports.action_report_tax_withheld').report_action(self.payslip_ids)

    def action_print_pension_contribution(self):
        pays_pension = self.payslip_ids.filtered(
            lambda p: p.employee_id.pays_pension)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Branch',
            'res_model': 'social.contribution.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_ids': [(6, 0, pays_pension.ids)],
                'default_is_pension': True,
            }
        }
        # return self.env.ref('custom_payslip_reports.action_report_pension_contribution').report_action(self.payslip_ids)

    def action_print_saving_deduction(self):
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Select Branch',
        #     'res_model': 'social.contribution.wizard',
        #     'view_mode': 'form',
        #     'target': 'new',
        #     'context': {
        #         'default_payslip_ids': [(6, 0, self.payslip_ids.ids)],
        #         'default_is_saving': True,
        #     }
        # }
        return self.env.ref('custom_payslip_reports.action_report_saving_deduction').report_action(self.payslip_ids)

    def action_open_social_contribution_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Branch',
            'res_model': 'social.contribution.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payslip_ids': [(6, 0, self.payslip_ids.ids)],
            }
        }
