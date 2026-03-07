from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    discipline_amount = fields.Float(string='Discipline Amount')

    @api.onchange('struct_id', 'date_from', 'date_to', 'employee_id')
    def onchange_employee_discipline(self):
        """ to display the employee discipline in input type """

        for data in self:
            if (not data.employee_id) or (not data.date_from) or (not data.date_to):
                return
            viol = data.input_line_ids.filtered(lambda i:i.input_type_id.code == 'VIOL')
            if viol:
                for discipline in viol:
                    discipline.unlink()

    def input_data_discipline_line(self, amount):
        """ to return the employee discipline amount in input type """

        check_lines = []
        new_name = self.env['hr.payslip.input.type'].search([
            ('code', '=', 'VIOL')])
        for rec in new_name:
            line = (0, 0, {
                'input_type_id': rec.id,
                'amount': amount,
                'name': 'VIOL',
                'payslip_id':self.id
            })

        check_lines.append(line)
        return check_lines


    def compute_sheet(self):
        self.onchange_employee_discipline()
        self.update_input_list_discipline()
        res = super(HrPayslip, self).compute_sheet()
        return res

    def update_input_list_discipline(self):
        for rec in self:
            list_discipline = rec.get_employee_discipline_input_list()
            list = list_discipline
            _logger.log(25, 'list' + str(list))
            rec.input_line_ids = list

    def get_employee_discipline_input_list(self):
        """ to check the employee have discipline amount and append it in list"""

        list = []
        for data in self:
            if (not data.employee_id) or (not data.date_from) or (not data.date_to):
                return

            discipline_line = data.struct_id.rule_ids.filtered(
                lambda x: x.code == 'VIOL')
            if discipline_line:
                discipline_id = self.env['disciplinary.action'].search([
                    ('employee_name', '=', data.employee_id.id),
                    ('state', '=', 'action'),('discipline_date','>=',data.date_from),('discipline_date','<=',data.date_to)
                ])
                if discipline_id:
                    total = 0
                    for vi in discipline_id:
                        total += vi.amount
                    # amount = ((data.contract_id.wage / 30) * total) + vi.amount
                    list = data.input_data_discipline_line(total)
        return list


class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    input_id = fields.Many2one('hr.salary.rule')


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    company_id = fields.Many2one('res.company', 'Company', copy=False, readonly=True, help="Comapny",
                                 default=lambda self: self.env.user.company_id)


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    company_id = fields.Many2one('res.company', 'Company', copy=False, readonly=True, help="Comapny",
                                 default=lambda self: self.env.user.company_id)