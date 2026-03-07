from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

import logging


class EmployeeDeductionType(models.Model):
    _name = 'employee.deduction.type'
    _description = 'Employee Deduction Type'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True,
                       help="The code used for the salary rule input.")
    input_type_id = fields.Many2one(
        'hr.payslip.input.type', string="Payslip Input Type",
        readonly=True, copy=False)
    salary_rule_id = fields.Many2one(
        'hr.salary.rule', string="Salary Rule",
        readonly=True, copy=False)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "The Code must be unique!"),
    ]

    @api.model
    def create(self, vals):
        # First, create the deduction type record itself
        deduction_type = super(EmployeeDeductionType, self).create(vals)

        # Now, create the corresponding payroll records
        self._create_payroll_records(deduction_type)

        return deduction_type

    def write(self, vals):
        # Update the deduction type
        res = super(EmployeeDeductionType, self).write(vals)

        # If the name or code was changed, update the linked payroll records
        if 'name' in vals or 'code' in vals:
            for rec in self:
                rec.salary_rule_id.write(
                    {'name': rec.name, 'code': f"DED_{rec.code}"})
                rec.input_type_id.write({'name': rec.name, 'code': rec.code})

        return res

    def unlink(self):
        # Before deleting the deduction type, delete its linked records
        for rec in self:
            rec.salary_rule_id.unlink()
            rec.input_type_id.unlink()

        return super(EmployeeDeductionType, self).unlink()

    def _create_payroll_records(self, deduction_type):
        """Helper method to create the input type and salary rule."""
        # Find the Salary Structure to add the rule to.
        # IMPORTANT: Replace this with the XML ID of YOUR structure from the previous step.
        structure = self.env.ref(
            'hr_payroll.structure_002', raise_if_not_found=False)
        if not structure:
            raise UserError(
                _("The Salary Structure was not found. Cannot create payroll records."))

        # Create the Payslip Input Type
        input_type = self.env['hr.payslip.input.type'].create({
            'name': deduction_type.name,
            'code': deduction_type.code,
        })

        # Create the Salary Rule
        salary_rule = self.env['hr.salary.rule'].create({
            'name': deduction_type.name,
            'code': f"DED_{deduction_type.code}",  # e.g., DED_MOBILE
            'category_id': self.env.ref('hr_payroll.DED').id,
            'sequence': 195,
            'struct_id': structure.id,
            'condition_select': 'python',
            'condition_python': f"result = '{deduction_type.code}' in inputs",
            'amount_select': 'code',
            'amount_python_compute': f"result = inputs['{deduction_type.code}'].amount",
        })

        # Link them back to the deduction type for future reference
        deduction_type.write({
            'input_type_id': input_type.id,
            'salary_rule_id': salary_rule.id,
        })

class EmployeeDeduction(models.Model):
    _name = 'employee.deduction'
    _description = 'Employee Ad-hoc Deduction'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Description", required=True, tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', string="Employee", required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', 
        related='employee_id.company_id',
        store=True,
        readonly=True) 
    deduction_type_id = fields.Many2one(
        'employee.deduction.type', string="Deduction Type", required=True, tracking=True)
    amount = fields.Float(string="Amount", required=True, tracking=True)
    date = fields.Date(
        string="Date", default=fields.Date.context_today, required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('applied', 'Applied to Payslip'),
        ('rejected', 'Rejected'),
    ], string="State", default='draft', tracking=True)

    payslip_id = fields.Many2one('hr.payslip', string="Payslip", readonly=True)
    date = fields.Date()
    is_latest_month = fields.Boolean(compute='_compute_is_latest_month', store=True, index=True)

    # --- Workflow Actions ---
    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
    def _compute_is_latest_month(self):
        if not self:
            return
        # Get the highest date in the model
        max_date = self.search([], order='date desc', limit=1).date
        if not max_date:
            return
        month_start = max_date.replace(day=1)
        next_month_start = (month_start + relativedelta(months=1))
        for rec in self:
            rec.is_latest_month = month_start <= rec.date < next_month_start

   