# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BudgetProjectPlan(models.Model):
    _name = 'corporate.planning.budget.project'
    _description = 'Project Budget Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Plan Title', required=True, default='New Project Plan')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    
    fiscal_year = fields.Char(string='Budget Year', required=True, default=lambda self: str(fields.Date.today().year + 1))
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account', 
        required=True
    )
    linked_budget_id = fields.Many2one(
        'budget.analytic', 
        string='Add to Existing Budget',
        domain="[('company_id', '=', company_id)]"
    )
    
    line_ids = fields.One2many('corporate.planning.budget.project.line', 'plan_id', string='Project Components')
    
    # Header Total
    total_project_budget = fields.Float(string='Total Annual Project Budget', compute='_compute_total', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    @api.depends('line_ids.budget_amount')
    def _compute_total(self):
        for plan in self:
            plan.total_project_budget = sum(line.budget_amount for line in plan.line_ids)

    # Workflow Buttons
    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_approve(self):
        self.write({'state': 'approved'})
        self._create_analytic_budget()

    def action_reset_draft(self):
        self.write({'state': 'draft'})
        
    def action_cancel(self):
        self.write({'state': 'cancelled'})
        
    def _create_analytic_budget(self):
        if 'budget.analytic' not in self.env or 'budget.line' not in self.env:
            return

        BudgetParent = self.env['budget.analytic']
        BudgetLine = self.env['budget.line']

        for plan in self:
            if not plan.analytic_account_id:
                continue

            if plan.linked_budget_id:
                budget_id = plan.linked_budget_id.id
            else:
                parent_vals = {
                    'name': f"{plan.name} ({plan.fiscal_year})",
                    'date_from': plan.date_from,
                    'date_to': plan.date_to,
                    'company_id': plan.company_id.id,
                }
                new_budget = BudgetParent.create(parent_vals)
                budget_id = new_budget.id

            line_vals = {
                'budget_analytic_id': budget_id,
                'account_id': plan.analytic_account_id.id,
                'budget_amount': plan.total_project_budget,
                'date_from': plan.date_from,
                'date_to': plan.date_to,
                'company_id': plan.company_id.id,
            }
            BudgetLine.create(line_vals)
            plan.message_post(body=f"✅ Project Budget integrated.")



class BudgetProjectLine(models.Model):
    _name = 'corporate.planning.budget.project.line'
    _description = 'Project Budget Line Item'
    _order = 'sequence, id'

    plan_id = fields.Many2one('corporate.planning.budget.project', string='Project Plan')
    sequence = fields.Integer(string='Sequence', default=10)
    
    # This field handles the "Mekelle Factory" vs "Workshop" distinction
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')
    ], default=False, help="Technical field for UX purpose.")

    name = fields.Char(string='Component / Block', required=True)
    
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Unit (SI)')
    
    start_date = fields.Date(string='Est. Start')
    end_date = fields.Date(string='Est. Completion')
    
    expense_type = fields.Selection([
        ('capex', 'CAPEX (Investment)'),
        ('opex', 'OPEX (Operational)')
    ], string='Type')
    current_status = fields.Char(string='Current Status', help="e.g. 92% physically completed")
    
    budget_amount = fields.Float(string='Budget (ETB)')
    
    remark = fields.Char(string='Remark')