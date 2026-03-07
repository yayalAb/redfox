# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HRBudgetWizard(models.TransientModel):
    _name = 'corporate.budget.hr.wizard'
    _description = 'Wizard to Add Employees to HR Budget'

    plan_id = fields.Many2one('corporate.planning.budget.hr', required=True)
    department_id = fields.Many2one('hr.department', string="Filter Department")
    
    employee_ids = fields.Many2many(
        'hr.employee', 
        string="Select Employees",
        domain="[('department_id', 'child_of', department_id)]"
    )
    
    increment_percentage = fields.Float(string="Apply Increment (%)", default=0.0)

    def action_add_employees(self):
        LineModel = self.env['corporate.planning.budget.hr.line']
        
        for wizard in self:
            for emp in wizard.employee_ids:
                # 1. Fetch Contract Data
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'open')
                ], limit=1)

                wage = contract.wage if contract else 0.0
                
                # 2. Apply Increment
                if wizard.increment_percentage > 0:
                    wage = wage * (1 + wizard.increment_percentage / 100)

                # 3. Create Line
                LineModel.create({
                    'plan_id': wizard.plan_id.id,
                    'employee_id': emp.id,
                    'basic_salary': wage,
                    # Optional: Add logic to fetch other allowances from contract fields
                    # 'transport_allowance': contract.transport_allowance, etc.
                })