# -*- coding: utf-8 -*-
from odoo import models, fields, api

# --- 1. THE MAIN DOCUMENT (Parent) ---
class CorporateStrategyDocument(models.Model):
    _name = 'corporate.strategy.document'
    _description = '5-Year Strategic Plan Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Strategy Title', required=True, default="Strategic Plan 2025-2030")
    start_year = fields.Char(string='Start Year', required=True, default=2025)
    end_year = fields.Char(string='End Year', required=True, default=2030)
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Document Upload
    strategy_doc_file = fields.Binary(string="Signed Strategy Document (PDF)")
    filename = fields.Char(string="Filename")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Approval'),
        ('active', 'Active Strategy'),
        ('closed', 'Closed/Archived')
    ], default='draft', tracking=True)
    
    def action_submit_for_approval(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'active'})

    def action_revise(self):
        self.write({'state': 'draft'})
    
    vision = fields.Html(string='Vision Statement', help="The long-term aspiration of the company.")
    mission = fields.Html(string='Mission Statement', help="The core purpose of the company.")
    
    # Relation to the new Core Values table
    core_value_ids = fields.One2many('corporate.strategy.core.value', 'document_id', string='Core Values')

    # RELATIONS
    pillar_ids = fields.One2many('corporate.strategy.core.pillar', 'document_id', string='Strategic Pillars')
    goal_ids = fields.One2many('corporate.strategy.goal', 'document_id', string='Strategic Goals')
    
    # BSC Implementation Matrix
    bsc_impl_ids = fields.One2many('corporate.strategy.bsc.impl', 'document_id', string='BSC Implementation Plan')
    
    # Financial Forecasts
    revenue_forecast_ids = fields.One2many('corporate.strategy.finance.forecast', 'document_id', string='Revenue Forecast', domain=[('type','=','revenue')])
    expense_forecast_ids = fields.One2many('corporate.strategy.finance.forecast', 'document_id', string='Expense Forecast', domain=[('type','=','expense')])

    def write(self, vals):
        res = super(CorporateStrategyDocument, self).write(vals)
        if 'bsc_impl_ids' in vals:
            self._sync_bsc_sections()
        return res

    @api.model
    def create(self, vals):
        record = super(CorporateStrategyDocument, self).create(vals)
        if 'bsc_impl_ids' in vals:
            record._sync_bsc_sections()
        return record

    # --- THE LOGIC ---
    def _sync_bsc_sections(self):
        """ 
        Iterates through the list in order.
        1. If it hits a Perspective Header, it updates the 'current_perspective'.
        2. If it hits a Goal Header, it updates the 'current_goal'.
        3. If it hits a Data Line, it saves those values onto the line.
        """
        for doc in self:
            current_perspective_id = False
            current_goal_id = False
            
            # Ensure we process in the order seen on screen (Sequence)
            # using .sorted() ensures the logic flows top-to-bottom
            sorted_lines = doc.bsc_impl_ids.sorted(key=lambda r: r.sequence)

            for line in sorted_lines:
                
                # CASE 1: PERSPECTIVE HEADER
                if line.row_type == 'perspective':
                    current_perspective_id = line.bsc_perspective.id
                    # When a new Perspective starts, usually the Goal resets
                    current_goal_id = False 
                
                # CASE 2: GOAL HEADER
                elif line.row_type == 'goal':
                    current_goal_id = line.goal_id.id
                
                # CASE 3: DATA LINE
                elif line.row_type == 'data':
                    # Prepare dictionary of updates
                    vals_to_write = {}
                    
                    # Only write if the value is different (Performance optimization)
                    if current_perspective_id and line.bsc_perspective.id != current_perspective_id:
                        vals_to_write['bsc_perspective'] = current_perspective_id
                    
                    if current_goal_id and line.goal_id.id != current_goal_id:
                        vals_to_write['goal_id'] = current_goal_id
                    
                    # Apply updates
                    if vals_to_write:
                        line.write(vals_to_write)

class StrategyCoreValue(models.Model):
    _name = 'corporate.strategy.core.value'
    _description = 'Strategic Core Value'
    _order = 'sequence, id'

    document_id = fields.Many2one('corporate.strategy.document', string='Strategy Document')
    sequence = fields.Integer(default=10)
    
    name = fields.Char(string='Value', required=True, help="e.g. Integrity, Innovation")
    description = fields.Text(string='Description', required=True, help="What this value means to us.")

# --- 2. STRATEGIC PILLARS ---
class StrategyCorePillar(models.Model):
    _name = 'corporate.strategy.core.pillar'
    _description = 'Strategic Core Pillar'

    document_id = fields.Many2one('corporate.strategy.document')
    name = fields.Char(string='Pillar Name', required=True)
    description = fields.Text(string='Description')
    strategic_outcomes = fields.Text(string='Strategic Outcomes')
    key_strategy = fields.Text(string='Key Strategy')


# --- 3. STRATEGIC GOALS & OBJECTIVES ---
class StrategyGoal(models.Model):
    _name = 'corporate.strategy.goal'
    _description = 'Strategic Goal'

    document_id = fields.Many2one('corporate.strategy.document')
    name = fields.Char(string='Strategic Goal', required=True)
    
    # Incentives for achieving this goal
    strategy_description = fields.Text(string='Strategiy Description')
    linked_pillar_id = fields.Many2one('corporate.strategy.core.pillar', string='Linked Strategic Pillar')
    
    
    # Sub-Objectives (One2many)
    objective_ids = fields.One2many('corporate.strategy.objective', 'goal_id', string='Strategic Objectives (SMART)')

class StrategyObjective(models.Model):
    _name = 'corporate.strategy.objective'
    _description = 'SMART Strategic Objective'

    goal_id = fields.Many2one('corporate.strategy.goal')
    name = fields.Char(string='Objective (SMART)', required=True)
    key_results = fields.Many2many('corporate.strategy.key.result', string='Key Results')
    kpi_id = fields.Many2many('appraisal.kpi', string='KPI (Metric)')
    description = fields.Text(string='Description')
    key_initiatives = fields.Text(string='Key Initiatives')

class KeyResult(models.Model):
    _name = 'corporate.strategy.key.result'
    _description = 'Key Result for Strategic Objective'

    objective_id = fields.Many2one('corporate.strategy.objective', string='Strategic Objective')
    name = fields.Char(string='Key Result', required=True)
    target_value = fields.Float(string='Target Value')
    current_value = fields.Float(string='Current Value')
    progress_percentage = fields.Float(string='Progress (%)', compute='_compute_progress_percentage', store=True)

    @api.depends('target_value', 'current_value')
    def _compute_progress_percentage(self):
        for kr in self:
            if kr.target_value > 0:
                kr.progress_percentage = (kr.current_value / kr.target_value) * 100
            else:
                kr.progress_percentage = 0.0

# --- 4. BSC IMPLEMENTATION PLAN (5 Years) ---
class BSCImplementation(models.Model):
    _name = 'corporate.strategy.bsc.impl'
    _description = 'BSC Implementation Matrix'
    _order = 'sequence, id'
    
    sequence = fields.Integer(default=10)

    document_id = fields.Many2one('corporate.strategy.document')
    
    row_type = fields.Selection([
        ('perspective', 'Perspective Section'),
        ('goal', 'Strategic Goal Section'),
        ('data', 'KPI Data Line')
    ], default='data', required=True)
    
    bsc_perspective = fields.Many2one('corporate.bsc.perspective', string='Perspective')

    # Link to the Goals defined above
    goal_id = fields.Many2one('corporate.strategy.objective', string='Strategic Goal')
    
    key_activities = fields.Text(string='Key Activities')
    kpi_id = fields.Many2one('appraisal.kpi', string='KPI')
    
    baseline = fields.Float(string='Baseline')
    target_long_term = fields.Float(string='Target (End of Period)')
    
    # 5 Year Breakdown
    y1_target = fields.Float(string='Year 1')
    y2_target = fields.Float(string='Year 2')
    y3_target = fields.Float(string='Year 3')
    y4_target = fields.Float(string='Year 4')
    y5_target = fields.Float(string='Year 5')
    
    name = fields.Char(string='Label', compute='_compute_name', store=True)

    @api.depends('goal_id')
    def _compute_name(self):
        for line in self:
            # if line.row_type == 'bsc_perspective' and line.bsc_perspective:
            #     # Simply get the name of the selected record
            #     line.name = line.bsc_perspective.name

            if line.goal_id:
                # Simply get the name of the selected record
                line.name = line.goal_id.name
            
            # else:
            #     line.name = "/"


# --- 5. FINANCIAL FORECAST (Revenue & Expense) ---
class FinancialForecast(models.Model):
    _name = 'corporate.strategy.finance.forecast'
    _description = '5-Year Financial Forecast'

    document_id = fields.Many2one('corporate.strategy.document')
    
    type = fields.Selection([('revenue', 'Revenue'), ('expense', 'Expense')], string='Type', required=True)
    
    # Business Unit (Company or Department)
    business_unit_id = fields.Many2one('res.company', string='Business Unit/Company')
    
    source_of_fund = fields.Char(string='Source of Finance/Fund')
    kpi_id = fields.Many2one('appraisal.kpi', string='KPI (Metric)')
    
    baseline = fields.Float(string='Baseline')
    target_long_term = fields.Float(string='Target (End of Period)')
    
    y1_value = fields.Float(string='Year 1')
    y2_value = fields.Float(string='Year 2')
    y3_value = fields.Float(string='Year 3')
    y4_value = fields.Float(string='Year 4')
    y5_value = fields.Float(string='Year 5')