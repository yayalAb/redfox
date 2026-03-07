# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class CorporatePerformanceReport(models.Model):
    _name = 'corporate.performance.report'
    _description = 'Quarterly Performance Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Report Title', required=True, default='New Performance Report')
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    
    # Link to the Plan 
    plan_id = fields.Many2one('corporate.operating.plan', string='Linked Annual Plan', 
                              domain="[('department_id', '=', department_id), ('state', '=', 'approved')]", required=True)
    
    fiscal_year = fields.Char(related='plan_id.fiscal_year', store=True)
    
    quarter = fields.Selection([
        ('q1', 'Quarter 1 (July - Sept)'),
        ('q2', 'Quarter 2 (Oct - Dec)'),
        ('q3', 'Quarter 3 (Jan - Mar)'),
        ('q4', 'Quarter 4 (Apr - Jun)'),
    ], string='Reporting Quarter', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Data Generated'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved')
    ], default='draft', tracking=True)

    # --- Performance Lines ---
    # Renamed to avoid conflict with mail.activity.mixin
    op_activity_ids = fields.One2many('corporate.performance.activity', 'report_id', string='Activity Performance')
    financial_ids = fields.One2many('corporate.performance.financial', 'report_id', string='Financial Performance')
    kpi_ids = fields.One2many('corporate.performance.kpi', 'report_id', string='KPI Performance')
    capex_ids = fields.One2many('corporate.performance.capex', 'report_id', string='Capex Performance')

    # --- INTELLIGENT FETCH BUTTON ---
    def action_generate_data(self):
        if not self.plan_id or not self.quarter:
            raise UserError("Select Plan and Quarter.")

        # Clean existing
        self.op_activity_ids.unlink()
        self.financial_ids.unlink()
        self.kpi_ids.unlink()
        self.capex_ids.unlink()

        # --- 1. BUILD LOOKUP MAPS USING IDs ---
        # Key = Database ID (Integer), Value = Data Dictionary
        ly_activity_map = {}  
        ly_financial_map = {}
        ly_kpi_map = {}
        ly_capex_map = {}

        if self.plan_id.previous_plan_id:
            prev_report = self.env['corporate.performance.report'].search([
                ('plan_id', '=', self.plan_id.previous_plan_id.id),
                ('quarter', '=', self.quarter),
                ('state', 'in', ['submitted', 'approved'])
            ], limit=1)

            if prev_report:
                # Map using the MASTER ID (.id), not the string name
                for line in prev_report.op_activity_ids:
                    if line.activity_master_id:
                        ly_activity_map[line.activity_master_id.id] = {'plan': line.quarter_plan, 'actual': line.quarter_actual}
                
                for line in prev_report.financial_ids:
                    if line.item_id:
                        ly_financial_map[line.item_id.id] = {'plan': line.quarter_plan_amount, 'actual': line.quarter_actual_amount}
                
                for line in prev_report.kpi_ids:
                    if line.kpi_id:
                        ly_kpi_map[line.kpi_id.id] = {'target': line.quarter_target, 'actual': line.quarter_actual}
                        
                for line in prev_report.capex_ids:
                    if line.capex_item_id:
                        ly_capex_map[line.capex_item_id.id] = {
                            'plan_qty': line.quarter_plan_qty, 'act_qty': line.quarter_actual_qty,
                            'budget': line.quarter_budget_etb, 'cost': line.quarter_actual_cost
                        }

        # --- 2. GENERATE CURRENT LINES AND MATCH ---
        
        # A. Activity
        for line in self.plan_id.op_activity_ids:
            target = self._get_quarter_sum(line) # (Helper function assumed)
            
            # MATCHING LOGIC: Use the ID of the master record
            ly = ly_activity_map.get(line.activity_master_id.id, {'plan': 0.0, 'actual': 0.0})

            self.env['corporate.performance.activity'].create({
                'report_id': self.id,
                'activity_master_id': line.activity_master_id.id, # Link to Master
                'uom_id': line.uom_id.id,
                'annual_target': line.annual_target,
                'quarter_plan': target,
                'ly_quarter_plan': ly['plan'],
                'ly_quarter_actual': ly['actual'],
            })

        # B. Financial
        for line in self.plan_id.financial_ids:
            target = self._get_quarter_sum(line)
            ly = ly_financial_map.get(line.item_id.id, {'plan': 0.0, 'actual': 0.0})

            self.env['corporate.performance.financial'].create({
                'report_id': self.id,
                'item_id': line.item_id.id, # Link to Master
                'category': line.category,
                'uom_id': line.uom_id.id,
                'annual_budget': line.annual_budget,
                'quarter_plan_amount': target,
                'ly_quarter_plan': ly['plan'],
                'ly_quarter_actual': ly['actual'],
            })

        # C. KPI
        for line in self.plan_id.kpi_ids:
            target = self._get_quarter_sum(line)
            ly = ly_kpi_map.get(line.kpi_id.id, {'target': 0.0, 'actual': 0.0})

            self.env['corporate.performance.kpi'].create({
                'report_id': self.id,
                'kpi_id': line.kpi_id.id, # Link to Master
                'perspective': line.perspective,
                'weight': line.weight,
                'annual_target': line.annual_target,
                'quarter_target': target,
                'ly_quarter_target': ly['target'],
                'ly_quarter_actual': ly['actual'],
            })

        # 6. GENERATE CAPEX LINES
        for line in self.plan_id.capex_ids:
            q_qty = 0.0
            q_budget = 0.0
            if self.quarter == 'q1': 
                q_qty = line.q1_qty
                q_budget = line.q1_budget
            elif self.quarter == 'q2': 
                q_qty = line.q2_qty
                q_budget = line.q2_budget
            elif self.quarter == 'q3': 
                q_qty = line.q3_qty
                q_budget = line.q3_budget
            elif self.quarter == 'q4': 
                q_qty = line.q4_qty
                q_budget = line.q4_budget

            ly = ly_capex_map.get(line.capex_item_id.id, {'plan_qty':0, 'act_qty':0, 'budget':0, 'cost':0})

            self.env['corporate.performance.capex'].create({
                'report_id': self.id,
                'capex_item_id': line.capex_item_id.id, # Link to Master
                'annual_plan_qty': line.annual_target_qty,
                'annual_budget_etb': line.annual_budget_etb,
                'quarter_plan_qty': q_qty,
                'quarter_budget_etb': q_budget,
                'ly_quarter_plan_qty': ly['plan_qty'],
                'ly_quarter_actual_qty': ly['act_qty'],
                'ly_quarter_budget': ly['budget'],
                'ly_quarter_cost': ly['cost'],
            })
            
        self.write({'state': 'generated'})
    
    def _get_quarter_sum(self, line):
        if self.quarter == 'q1': return sum([line.m1, line.m2, line.m3])
        if self.quarter == 'q2': return sum([line.m4, line.m5, line.m6])
        if self.quarter == 'q3': return sum([line.m7, line.m8, line.m9])
        if self.quarter == 'q4': return sum([line.m10, line.m11, line.m12])
        return 0.0

    def action_submit(self):
        self.write({'state': 'submitted'})
    def action_approve(self):
        self.write({'state': 'approved'})


# --- 1. ACTIVITY PERFORMANCE LINE ---
class PerformanceActivity(models.Model):
    _name = 'corporate.performance.activity'
    _description = 'Activity Performance Line'

    report_id = fields.Many2one('corporate.performance.report')
    

    activity_master_id = fields.Many2one(
            'corporate.activity.master', 
            string='Objective / Activity', 
            required=True,
            domain="[('department_id', '=', parent.department_id)]"
        )
    
    uom_id = fields.Many2one('uom.uom', string='UOM')
    
    annual_target = fields.Float(string='Annual Target', readonly=True)
    
    # Last Year Comparison
    last_year_actual = fields.Float(string='Last Year Q Actual')
    ly_quarter_plan = fields.Float(string='LY Plan')
    ly_quarter_actual = fields.Float(string='LY Actual')
    ly_percent_achieved = fields.Float(string='LY %', compute='_compute_ly_metrics', store=True)
    
    # Current Quarter Performance
    quarter_plan = fields.Float(string='Quarter Plan', readonly=True)
    quarter_actual = fields.Float(string='Quarter Actual')
    
    # Computed
    percent_achieved = fields.Float(string='% Achieved', compute='_compute_metrics', store=True)
    variance = fields.Float(string='Variance', compute='_compute_metrics', store=True)
    
    remark = fields.Char(string='Remarks')
    
    
    # --- REPORTING FIELDS (Stored for Pivot/Graph Grouping) ---
    department_id = fields.Many2one(related='report_id.department_id', store=True, string="Department")
    fiscal_year = fields.Char(related='report_id.fiscal_year', store=True, string="Fiscal Year")
    quarter = fields.Selection(related='report_id.quarter', store=True, string="Quarter")
    state = fields.Selection(related='report_id.state', store=True, string="Status")

    @api.depends('ly_quarter_plan', 'ly_quarter_actual')
    def _compute_ly_metrics(self):
        for line in self:
            if line.ly_quarter_plan > 0:
                line.ly_percent_achieved = (line.ly_quarter_actual / line.ly_quarter_plan) * 100
            else:
                line.ly_percent_achieved = 0.0

    @api.depends('quarter_plan', 'quarter_actual')
    def _compute_metrics(self):
        for line in self:
            line.variance = line.quarter_actual - line.quarter_plan
            if line.quarter_plan > 0:
                line.percent_achieved = (line.quarter_actual / line.quarter_plan) * 100
            else:
                line.percent_achieved = 0.0


# --- 2. FINANCIAL PERFORMANCE LINE ---
class PerformanceFinancial(models.Model):
    _name = 'corporate.performance.financial'
    _description = 'Financial Performance Line'

    report_id = fields.Many2one('corporate.performance.report')

    item_id = fields.Many2one(
        'corporate.financial.item', 
        string='Budget Line Item', 
        required=True,
        domain="[('department_id', '=', parent.department_id)]"
    )
    
    category = fields.Selection([
        ('revenue', 'Revenue'),
        ('cos', 'Cost of Sales'),
        ('opex', 'Operating Expenses'),
        ('other', 'Other')
    ], string='Category', readonly=True)
    
    uom_id = fields.Many2one('uom.uom', string='UOM')
    annual_budget = fields.Float(string='Annual Budget', readonly=True)
    
    # Last Year
    last_year_actual = fields.Float(string='LY Actual')
    ly_quarter_plan = fields.Float(string='LY Plan')
    ly_quarter_actual = fields.Float(string='LY Actual')
    ly_percent_utilization = fields.Float(string='LY %', compute='_compute_ly_metrics', store=True)
    
    # This Quarter
    quarter_plan_amount = fields.Float(string='Plan', readonly=True)
    quarter_actual_amount = fields.Float(string='Actual')
    
    percent_utilization = fields.Float(string='% Utilized', compute='_compute_metrics', store=True)
    variance_amount = fields.Float(string='Variance', compute='_compute_metrics', store=True)
    
    remark = fields.Char(string='Remarks')
    
    # --- REPORTING FIELDS (Stored for Pivot/Graph Grouping) ---
    department_id = fields.Many2one(related='report_id.department_id', store=True, string="Department")
    fiscal_year = fields.Char(related='report_id.fiscal_year', store=True, string="Fiscal Year")
    quarter = fields.Selection(related='report_id.quarter', store=True, string="Quarter")
    state = fields.Selection(related='report_id.state', store=True, string="Status")

    @api.depends('ly_quarter_plan', 'ly_quarter_actual')
    def _compute_ly_metrics(self):
        for line in self:
            if line.ly_quarter_plan > 0:
                line.ly_percent_utilization = (line.ly_quarter_actual / line.ly_quarter_plan) * 100
            else:
                line.ly_percent_utilization = 0.0

    @api.depends('quarter_plan_amount', 'quarter_actual_amount')
    def _compute_metrics(self):
        for line in self:
            line.variance_amount = line.quarter_actual_amount - line.quarter_plan_amount
            if line.quarter_plan_amount > 0:
                line.percent_utilization = (line.quarter_actual_amount / line.quarter_plan_amount) * 100
            else:
                line.percent_utilization = 0.0


# --- 3. KPI PERFORMANCE LINE ---
class PerformanceKPI(models.Model):
    _name = 'corporate.performance.kpi'
    _description = 'KPI Performance Line'

    report_id = fields.Many2one('corporate.performance.report')
    perspective = fields.Char(string='Perspective', readonly=True)

    kpi_id = fields.Many2one(
        'appraisal.kpi', 
        string='KPI', 
        required=True,
        domain="['|', ('department_id', '=', False), ('department_id', '=', parent.department_id)]"
    )
    
    weight = fields.Float(string='Weight')
    annual_target = fields.Float(string='Annual Target', readonly=True)
    
    # Last Year
    last_year_actual = fields.Float(string='LY Actual')
    ly_quarter_target = fields.Float(string='LY Target')
    ly_quarter_actual = fields.Float(string='LY Actual')
    ly_percent_achieved = fields.Float(string='LY %', compute='_compute_ly_metrics', store=True)
    
    # This Quarter
    quarter_target = fields.Float(string='Target', readonly=True)
    quarter_actual = fields.Float(string='Actual')
    
    percent_achieved = fields.Float(string='% Achieved', compute='_compute_metrics', store=True)
    
    remark = fields.Char(string='Remarks')
    
    # --- REPORTING FIELDS (Stored for Pivot/Graph Grouping) ---
    department_id = fields.Many2one(related='report_id.department_id', store=True, string="Department")
    fiscal_year = fields.Char(related='report_id.fiscal_year', store=True, string="Fiscal Year")
    quarter = fields.Selection(related='report_id.quarter', store=True, string="Quarter")
    state = fields.Selection(related='report_id.state', store=True, string="Status")

    @api.depends('ly_quarter_target', 'ly_quarter_actual')
    def _compute_ly_metrics(self):
        for line in self:
            if line.ly_quarter_target > 0:
                line.ly_percent_achieved = (line.ly_quarter_actual / line.ly_quarter_target) * 100
            else:
                line.ly_percent_achieved = 0.0

    @api.depends('quarter_target', 'quarter_actual')
    def _compute_metrics(self):
        for line in self:
            if line.quarter_target > 0:
                line.percent_achieved = (line.quarter_actual / line.quarter_target) * 100
            else:
                line.percent_achieved = 0.0


# --- 4. CAPEX PERFORMANCE LINE ---
class PerformanceCapex(models.Model):
    _name = 'corporate.performance.capex'
    _description = 'Capex Performance Line'

    report_id = fields.Many2one('corporate.performance.report')

    capex_item_id = fields.Many2one(
        'corporate.capex.item', 
        string='Objective / Asset', 
        required=True,
        domain="[('department_id', '=', parent.department_id)]"
    )
    
    annual_plan_qty = fields.Float(string='Annual Qty', readonly=True)
    annual_budget_etb = fields.Float(string='Annual Budget', readonly=True)
    
    # Last Year
    ly_quarter_plan_qty = fields.Float(string='LY Plan Qty')
    ly_quarter_actual_qty = fields.Float(string='LY Actual Qty')
    ly_qty_achieved = fields.Float(string='LY Qty %', compute='_compute_ly_metrics', store=True)

    ly_quarter_budget = fields.Float(string='LY Budget')
    ly_quarter_cost = fields.Float(string='LY Cost')
    ly_budget_utilized = fields.Float(string='LY Budget %', compute='_compute_ly_metrics', store=True)

    # Activity (Physical) Performance
    quarter_plan_qty = fields.Float(string='Plan Qty', readonly=True)
    quarter_actual_qty = fields.Float(string='Actual Qty')
    qty_achieved_percent = fields.Float(string='% Qty', compute='_compute_metrics', store=True)
    
    # Financial Performance
    quarter_budget_etb = fields.Float(string='Budget ETB', readonly=True)
    quarter_actual_cost = fields.Float(string='Actual Cost')
    budget_utilized_percent = fields.Float(string='% Budget', compute='_compute_metrics', store=True)
    
    user_department = fields.Char(string='User Dept')
    remark = fields.Char(string='Remarks')
    
    # --- REPORTING FIELDS (Stored for Pivot/Graph Grouping) ---
    department_id = fields.Many2one(related='report_id.department_id', store=True, string="Department")
    fiscal_year = fields.Char(related='report_id.fiscal_year', store=True, string="Fiscal Year")
    quarter = fields.Selection(related='report_id.quarter', store=True, string="Quarter")
    state = fields.Selection(related='report_id.state', store=True, string="Status")

    @api.depends('ly_quarter_plan_qty', 'ly_quarter_actual_qty', 'ly_quarter_budget', 'ly_quarter_cost')
    def _compute_ly_metrics(self):
        for line in self:
            if line.ly_quarter_plan_qty > 0:
                line.ly_qty_achieved = (line.ly_quarter_actual_qty / line.ly_quarter_plan_qty) * 100
            else:
                line.ly_qty_achieved = 0.0
            
            if line.ly_quarter_budget > 0:
                line.ly_budget_utilized = (line.ly_quarter_cost / line.ly_quarter_budget) * 100
            else:
                line.ly_budget_utilized = 0.0

    @api.depends('quarter_plan_qty', 'quarter_actual_qty', 'quarter_budget_etb', 'quarter_actual_cost')
    def _compute_metrics(self):
        for line in self:
            # Physical %
            if line.quarter_plan_qty > 0:
                line.qty_achieved_percent = (line.quarter_actual_qty / line.quarter_plan_qty) * 100
            else:
                line.qty_achieved_percent = 0.0
            
            # Financial %
            if line.quarter_budget_etb > 0:
                line.budget_utilized_percent = (line.quarter_actual_cost / line.quarter_budget_etb) * 100
            else:
                line.budget_utilized_percent = 0.0