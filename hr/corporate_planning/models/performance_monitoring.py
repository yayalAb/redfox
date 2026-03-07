from odoo import models, fields, api

class CorporatePerformanceReview(models.Model):
    _name = 'corporate.performance.review'
    _description = 'Performance Monitoring & Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Report Title', required=True, default='New Performance Report')
    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    fiscal_year = fields.Char(string='Fiscal Year', required=True)
    
    period = fields.Selection([
        ('q1', 'Quarter 1'),
        ('q2', 'Quarter 2'),
        ('q3', 'Quarter 3'),
        ('q4', 'Quarter 4'),
        ('annual', 'Annual Summary')
    ], string='Reporting Period', required=True)

    date_report = fields.Date(string='Report Date', default=fields.Date.context_today)

    # --- 1. KPI PERFORMANCE ---
    kpi_line_ids = fields.One2many('corporate.performance.kpi.line', 'review_id', string='KPI Progress')

    # --- 2. BUDGET UTILIZATION ---
    budget_line_ids = fields.One2many('corporate.performance.budget.line', 'review_id', string='Budget Utilization')

    # --- 3. PROJECT PROGRESS ---
    project_line_ids = fields.One2many('corporate.performance.project.line', 'review_id', string='Project Status')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved')
    ], default='draft', tracking=True)

    def action_submit(self):
        self.write({'state': 'submitted'})
    
    def action_approve(self):
        self.write({'state': 'approved'})


# --- KPI TRACKING LINES ---
class PerformanceKPILine(models.Model):
    _name = 'corporate.performance.kpi.line'
    _description = 'KPI Actual vs Target'

    review_id = fields.Many2one('corporate.performance.review')
    
    # Link to the Registry
    kpi_id = fields.Many2one('appraisal.kpi', string='KPI')
    weight = fields.Many2one('appraisal.kpi.weight', string='Weight', readonly=True)
    
    target_value = fields.Float(string='Planned Target')
    actual_value = fields.Float(string='Actual Achievement')
    
    variance = fields.Float(string='Variance', compute='_compute_variance', store=True)
    achievement_percent = fields.Float(string='Achievement %', compute='_compute_variance', store=True, group_operator="avg")

    @api.depends('target_value', 'actual_value')
    def _compute_variance(self):
        for line in self:
            line.variance = line.actual_value - line.target_value
            if line.target_value > 0:
                line.achievement_percent = (line.actual_value / line.target_value) * 100
            else:
                line.achievement_percent = 0.0


# --- BUDGET TRACKING LINES ---
class PerformanceBudgetLine(models.Model):
    _name = 'corporate.performance.budget.line'
    _description = 'Budget Actual vs Plan'

    review_id = fields.Many2one('corporate.performance.review')
    
    budget_type = fields.Selection([
        ('hr', 'Human Resources'),
        ('training', 'Training'),
        ('project', 'Project/Construction'),
        ('general', 'General/Assets')
    ], string='Budget Category', required=True)

    planned_amount = fields.Float(string='Planned Budget (Period)')
    actual_amount = fields.Float(string='Actual Spent')
    
    balance = fields.Float(string='Remaining Balance', compute='_compute_balance', store=True)
    burn_rate_percent = fields.Float(string='Utilization %', compute='_compute_balance', store=True, group_operator="avg")

    @api.depends('planned_amount', 'actual_amount')
    def _compute_balance(self):
        for line in self:
            line.balance = line.planned_amount - line.actual_amount
            if line.planned_amount > 0:
                line.burn_rate_percent = (line.actual_amount / line.planned_amount) * 100
            else:
                line.burn_rate_percent = 0.0


# --- PROJECT TRACKING LINES ---
class PerformanceProjectLine(models.Model):
    _name = 'corporate.performance.project.line'
    _description = 'Project Progress Status'

    review_id = fields.Many2one('corporate.performance.review')
    
    project_name = fields.Char(string='Project / Component')
    
    planned_status = fields.Char(string='Planned Status/Milestone')
    current_status = fields.Char(string='Current Status')
    
    completion_percent = fields.Float(string='% Completed', widget="percentage")
    
    status_indicator = fields.Selection([
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('delayed', 'Delayed')
    ], string='Health', default='on_track')
    
    remark = fields.Char(string='Issues / Blockers')