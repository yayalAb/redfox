from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PayslipRun(models.Model):
    _inherit = 'hr.salary.rule'
    is_basic = fields.Boolean(string='Is Base Rule')


class PayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_get_payslip_difference(self):

        payroll_diff_obj = self.env['payroll.difference.analysis']
        payroll_diff_obj.search([]).unlink()
        employee_ids = self.env['hr.employee'].search(
            [('active', 'in', [True, False])])
        previous_batch = self.env['hr.payslip.run'].search([
            ('id', '!=', self.id)], order='date_start desc', limit=1)
        previous_batch_id = False
        if previous_batch:
            previous_batch_id = previous_batch.id
        for emp in employee_ids:
            current_payslip = self.env['hr.payslip'].search([
                ('employee_id', '=', emp.id),
                ('payslip_run_id', '=', self.id)], limit=1)

            previous_payslip = self.env['hr.payslip'].search([
                ('employee_id', '=', emp.id),
                ('payslip_run_id', '=', previous_batch_id),
                ('date_from', '<', self.date_start)], order='date_from desc', limit=1)

            if current_payslip and previous_payslip:
                for line in current_payslip.line_ids:
                    previous_line = previous_payslip.line_ids.filtered(
                        lambda l: l.code == line.code)
                    if line.salary_rule_id.is_basic and previous_line and previous_line.total != line.total:
                        payroll_diff_obj.create({
                            'employee_id': emp.id,
                            'rule_id': line.salary_rule_id.id,
                            'month': f"{current_payslip.payslip_run_id.name} vs {previous_payslip.payslip_run_id.name}",
                            'late_month': previous_line.total,
                            'this_month': line.total,
                            'difference': line.total - previous_line.total
                        })
            elif current_payslip and not previous_payslip:
                for line in current_payslip.line_ids:
                    if line.salary_rule_id.is_basic and line.total != 0.0:
                        payroll_diff_obj.create({
                            'employee_id': emp.id,
                            'rule_id': line.salary_rule_id.id,
                            'month': current_payslip.payslip_run_id.name,
                            'late_month': 0.0,
                            'this_month': line.total,
                            'difference': line.total
                        })
            elif not current_payslip and previous_payslip:
                for line in previous_payslip.line_ids:
                    if line.salary_rule_id.is_basic and line.total != 0.0:
                        payroll_diff_obj.create({
                            'employee_id': emp.id,
                            'rule_id': line.salary_rule_id.id,
                            'month': previous_payslip.payslip_run_id.name,
                            'late_month': line.total,
                            'this_month': 0.0,
                            'difference': - line.total
                        })
        return {
            'name': 'Payroll Difference Analysis',
            'type': 'ir.actions.act_window',
            'res_model': 'payroll.difference.analysis',
            'view_mode': 'pivot,list',
            'target': 'current',
        }
        # 'context': "{'group_by': ['employee_id']}"


class PayrollDifferenceAnalysis(models.TransientModel):
    _name = 'payroll.difference.analysis'
    _description = 'Payroll Difference Analysis'
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True)
    rule_id = fields.Many2one(
        'hr.salary.rule', string='Salary Rule', required=True)
    month = fields.Char(string='Month', required=True)
    late_month = fields.Float(string='Late Month', required=True)
    this_month = fields.Float(string='This Month', required=True)
    difference = fields.Float(
        string='Difference')
