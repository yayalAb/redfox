# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BudgetTrainingPlan(models.Model):
    _name = 'corporate.planning.budget.training'
    _description = 'Annual Training Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Plan Title', required=True,tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    
    fiscal_year = fields.Char(string='Budget Year', required=True, default=lambda self: str(fields.Date.today().year + 1), tracking=True)
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)

    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account', 
        required=True,
        help="The Cost Center where this budget will be recorded."
    )
    
    linked_budget_id = fields.Many2one(
        'budget.analytic', 
        string='Add to Existing Budget',
        domain="[('company_id', '=', company_id)]",
        help="Select a Master Budget. If empty, a new one is created."
    )
    
    line_ids = fields.One2many('corporate.planning.budget.training.line', 'plan_id', string='Training Programs', tracking=True)
    
    total_budget = fields.Float(string='Total Training Budget', compute='_compute_total', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    @api.depends('line_ids.budget_amount')
    def _compute_total(self):
        for plan in self:
            plan.total_budget = sum(line.budget_amount for line in plan.line_ids)

    # --- WORKFLOW ACTION BUTTONS ---
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

            # LOGIC: Check if we append or create
            if plan.linked_budget_id:
                budget_id = plan.linked_budget_id.id
                budget_name = plan.linked_budget_id.name
            else:
                # Create New
                parent_vals = {
                    'name': f"{plan.name} ({plan.fiscal_year})",
                    'date_from': plan.date_from,
                    'date_to': plan.date_to,
                    'company_id': plan.company_id.id,
                }
                new_budget = BudgetParent.create(parent_vals)
                budget_id = new_budget.id
                budget_name = new_budget.name

            # Create Line
            line_vals = {
                'budget_analytic_id': budget_id,
                'account_id': plan.analytic_account_id.id,
                'budget_amount': plan.total_budget,
                'date_from': plan.date_from,
                'date_to': plan.date_to,
                'company_id': plan.company_id.id,
            }
            BudgetLine.create(line_vals)
            
            plan.message_post(body=f"✅ Added Training Budget line to: '{budget_name}'")


class BudgetTrainingLine(models.Model):
    _name = 'corporate.planning.budget.training.line'
    _description = 'Training Plan Line Item'
    _order = 'sequence, id'

    plan_id = fields.Many2one('corporate.planning.budget.training', string='Training Plan')
    sequence = fields.Integer(string='S.No', default=10)
    
    program_name = fields.Char(string='Program Name', required=True, tracking=True)
    
    training_content = fields.Html(string='Content of the Training')
    
    # CHANGED: Now links to the Employee list. Many2many allows selecting multiple people.
    participant_ids = fields.Many2many('hr.job', string='Training Participants')
    
    quantity = fields.Integer(string='Quantity', default=1)
    
    # NEW: Cost per unit/person
    unit_cost = fields.Float(string='Unit Cost')
    
    # CHANGED: Now computed based on Qty * Unit Cost
    budget_amount = fields.Float(string='Budget Amount', compute='_compute_amount', store=True)
    
    period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('bi_annually', 'Bi-Annually'),
        ('annually', 'Annually'),
        ('one_off', 'One-Off')
    ], string='Period', default='one_off')
    
    remark = fields.Char(string='Remark')

    @api.depends('quantity', 'unit_cost', 'period')
    def _compute_amount(self):
        for line in self:
            # 1. Determine Frequency Multiplier
            multiplier = 1
            if line.period == 'monthly':
                multiplier = 12
            elif line.period == 'quarterly':
                multiplier = 4
            elif line.period == 'bi_annually':
                multiplier = 2
            elif line.period == 'annually':
                multiplier = 1
            elif line.period == 'one_off':
                multiplier = 1
            
            
            line.budget_amount = line.quantity * line.unit_cost * multiplier