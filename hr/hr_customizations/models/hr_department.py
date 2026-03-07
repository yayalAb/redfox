from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    """added the description field as per the requirement"""
    description = fields.Text(
        string="Description",
        help="Additional notes or description about this department"
    )

    """added to check whether there are employees before deleting the dept and then creating error if there are."""
    # this method might require refactorring since it searchs every employee
    @api.ondelete(at_uninstall=False)
    def _restrict_delete_if_employees(self):
        employee_model = self.env['hr.employee']
        for dept in self:
            count = employee_model.search_count(
                [('department_id', '=', dept.id)])
            if count:
                raise UserError(_(
                    'Cannot delete Department "%s" because it has %d employee(s) assigned.'
                ) % (dept.name, count))

    """makes the department unique case insensitive (ci)"""
    @api.constrains('name', 'company_id')
    def _check_unique_department_name_ci(self):
        for dept in self:
            # search all other departments in the same company (exclude self)
            domain = [
                ('id', '!=', dept.id),
                ('name', 'like', dept.name),
                ('company_id', '=', dept.company_id.id),
            ]
            matching = self.search(domain)
            print("matching departments 00000000000000000000000000000000: ",
                  matching, self.env.company.id)
            for other in matching:
                if (other.name or '').strip().lower() == (dept.name or '').strip().lower():
                    raise ValidationError(_(
                        'A department named "%s" already exists in this company.\n'
                        'Department names must be unique within the same company (case-insensitive).'
                    ) % dept.name)
