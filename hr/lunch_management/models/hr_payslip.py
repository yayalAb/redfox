from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    lunch_line_ids = fields.Many2many(
        'lunch.log', string='Lunch', readonly=True)

    def compute_sheet(self):
        for data in self:
            if not data.employee_id or not data.date_from or not data.date_to:
                return super(HrPayslip, self).compute_sheet()

            # 1. Compute overtime total
            get_amount = self.env['lunch.log'].search([
                ('employee_id', '=', data.employee_id.id),
                ('state', '=', 'unbilled'),
                ('date', '>=', data.date_from),
                ('date', '<=', data.date_to)
            ])
            total = sum(get_amount.mapped('total_price'))
            if get_amount:
                data.lunch_line_ids = [(6, 0, get_amount.ids)]

            # 2. Ensure an input line OT100 exists on this payslip
            if total > 0:
                ot_input = data.input_line_ids.filtered(
                    lambda l: l.code == 'LUNCHDED')
                if ot_input:
                    ot_input.amount = total
                else:
                    data.input_line_ids = [(0, 0, {
                        'code': 'LUNCHDED',
                        'name': 'Lunch',
                        'amount': total,
                        'input_type_id': self.env.ref('lunch_management.hr_payroll_input_lunch').id,
                    })]
        return super(HrPayslip, self).compute_sheet()

    def action_payslip_done(self):
        """Mark loan as paid on paying payslip"""
        for slip in self:
            if slip.lunch_line_ids:
                slip.lunch_line_ids.write({'state': 'billed'})
        return super(HrPayslip, self).action_payslip_done()
