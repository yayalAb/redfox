# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CorporateOperationalPlan(models.Model):
    _name = 'corporate.planning.operational.plan'
    _description = 'Operational Plan & Monitoring'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Plan Title', required=True, default='New Operational Plan')
    
    # Context & Meta Data
    # Note: Ensure you have 'corporate.planning.annual.plan' model or remove this relation for testing
    annual_plan_id = fields.Many2one('corporate.planning.annual.plan', string='Linked Annual Plan')
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    fiscal_year = fields.Char(string='Fiscal Year', required=True, default=lambda self: str(fields.Date.today().year + 1))
    
    # --- TWO FIELDS FOR TWO TABS (Pointing to same model) ---
    
    # 1. Volume Based Lines (Strict Domain)
    volume_line_ids = fields.One2many(
        'corporate.planning.operational.plan.line', 
        'plan_id', 
        string='Volume Tasks', 
        domain=[('task_type', '=', 'volume')]
    )
    
    # 2. Checklist Based Lines (Strict Domain)
    discrete_line_ids = fields.One2many(
        'corporate.planning.operational.plan.line', 
        'plan_id', 
        string='Checklist Tasks', 
        domain=[('task_type', '=', 'discrete')]
    )

    # Performance Summary
    total_performance = fields.Float(string='Total Performance (%)', compute='_compute_performance', store=True)

    state = fields.Selection([
        ('draft', 'Planning Phase'),   # Plan is Editable, Actuals Readonly
        ('active', 'Execution Phase'), # Plan Readonly, Actuals Editable
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)

    @api.depends('volume_line_ids.weighted_score', 'discrete_line_ids.weighted_score')
    def _compute_performance(self):
        for plan in self:
            # Sum of scores from both tabs
            p1 = sum(line.weighted_score for line in plan.volume_line_ids)
            p2 = sum(line.weighted_score for line in plan.discrete_line_ids)
            plan.total_performance = p1 + p2

    def action_activate(self):
        self.write({'state': 'active'})
    
    def action_close(self):
        self.write({'state': 'closed'})
    
    def action_reset(self):
        self.write({'state': 'draft'})


class CorporateOperationalPlanLine(models.Model):
    _name = 'corporate.planning.operational.plan.line'
    _description = 'Operational Task Line'
    _order = 'sequence, id'

    plan_id = fields.Many2one('corporate.planning.operational.plan', string='Operational Plan')
    sequence = fields.Integer(string='S/No', default=10)

    # TYPE: Volume (Numeric) vs Discrete (Checklist)
    # Default is volume, but context in XML will override this for the second tab
    task_type = fields.Selection([
        ('volume', 'Volume Based'),
        ('discrete', 'Checklist Based')
    ], string='Task Type', required=True, default='volume')

    major_task = fields.Char(string='Major Task', required=True)
    specific_task = fields.Char(string='Specific Activity', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit')

    # --- PLANNING COLUMNS (Editable in Draft) ---
    q1_plan = fields.Float(string='Q1 Plan')
    q2_plan = fields.Float(string='Q2 Plan')
    q3_plan = fields.Float(string='Q3 Plan')
    q4_plan = fields.Float(string='Q4 Plan')
    total_plan = fields.Float(string='Annual Plan', compute='_compute_totals', store=True)

    # --- ACTUAL COLUMNS (Editable in Active) ---
    q1_actual = fields.Float(string='Q1 Actual')
    q2_actual = fields.Float(string='Q2 Actual')
    q3_actual = fields.Float(string='Q3 Actual')
    q4_actual = fields.Float(string='Q4 Actual')
    total_actual = fields.Float(string='Total Actual', compute='_compute_totals', store=True)

    # --- SCORING ---
    weight = fields.Float(string='Weight (%)', default=1.0)
    achievement_rate = fields.Float(string='Achieved %', compute='_compute_score', store=True)
    weighted_score = fields.Float(string='Score', compute='_compute_score', store=True)

    @api.depends('q1_plan', 'q2_plan', 'q3_plan', 'q4_plan', 
                 'q1_actual', 'q2_actual', 'q3_actual', 'q4_actual', 'task_type')
    def _compute_totals(self):
        for line in self:
            if line.task_type == 'volume':
                # Volume: Plan comes from user input
                line.total_plan = line.q1_plan + line.q2_plan + line.q3_plan + line.q4_plan
                line.total_actual = line.q1_actual + line.q2_actual + line.q3_actual + line.q4_actual
            else:
                # Checklist: Plan is implicitly 1.0 (It exists, so do it)
                # You could allow them to set a weight, but 'quantity' plan is just 1.
                line.total_plan = 1.0 
                
                # Actual is the sum of ticks (0.0 or 1.0 per quarter)
                # If they check multiple boxes, it might exceed 100%, which is usually fine (over-performance)
                line.total_actual = line.q1_actual + line.q2_actual + line.q3_actual + line.q4_actual

    @api.depends('total_plan', 'total_actual', 'weight', 'task_type')
    def _compute_score(self):
        for line in self:
            rate = 0.0
            if line.total_plan > 0:
                rate = (line.total_actual / line.total_plan) * 100
            
            # Cap at 100% for checklists? 
            # Usually if I do a task in Q1, I am done. 
            # If I check Q1 and Q2, is it 200%? Let's leave it as raw math for now.
            line.achievement_rate = rate
            line.weighted_score = (rate * line.weight) / 100
    