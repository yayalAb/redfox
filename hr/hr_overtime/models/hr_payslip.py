from odoo import models, api, fields
# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    overtime_line_ids = fields.Many2many(
        'overtime.calculator', string='Overtime', readonly=True)

    def compute_sheet(self):
        for data in self:
            if not data.employee_id or not data.date_from or not data.date_to:
                return super(HrPayslip, self).compute_sheet()

            # 1. Compute overtime total
            get_amount = self.env['overtime.calculator'].search([
                ('employee_id', '=', data.employee_id.id),
                ('start_date', '>=', data.date_from),
                ('end_date', '<=', data.date_to),
                ('state', '=', 'in_payment')
            ])
            total = sum(get_amount.mapped('value'))
            if get_amount:
                data.overtime_line_ids = [(6, 0, get_amount.ids)]

            # 2. Ensure an input line OT100 exists on this payslip
            if total > 0:
                ot_input = data.input_line_ids.filtered(
                    lambda l: l.code == 'OT100')
                if ot_input:
                    ot_input.amount = total
                else:
                    data.input_line_ids = [(0, 0, {
                        'code': 'OT100',
                        'name': 'Overtime',
                        'amount': total,
                        'input_type_id': self.env.ref('hr_overtime.hr_payroll_input_OT100').id,
                    })]
        return super(HrPayslip, self).compute_sheet()

    def action_payslip_done(self):
        """Mark loan as paid on paying payslip"""
        for slip in self:
            if slip.overtime_line_ids:
                slip.overtime_line_ids.write({'state': 'paid'})
        return super(HrPayslip, self).action_payslip_done()
