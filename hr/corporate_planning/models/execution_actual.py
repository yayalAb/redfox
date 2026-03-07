# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

# ==========================================
# 1. ACTIVITY EXECUTION ACTUALS
# ==========================================
class ExecutionActualActivity(models.Model):
    _name = 'corporate.execution.activity'
    _description = 'Activity Execution Actual (Source of Truth)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fiscal_year desc, period_month desc'
    
    name = fields.Char(compute='_compute_name', store=True)
    
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', required=True, index=True)
    
    fiscal_year = fields.Char(string='Fiscal Year', required=True, index=True)
    period_month = fields.Integer(required=True, string='Month (1-12)')
    period_quarter = fields.Selection([
        ('q1', 'Q1'), ('q2', 'Q2'), ('q3', 'Q3'), ('q4', 'Q4')
    ], compute='_compute_quarter', store=True)
    
    # Master Data Link
    activity_master_id = fields.Many2one('corporate.activity.master', required=True, index=True, string='Activity')
    uom_id = fields.Many2one('uom.uom', related='activity_master_id.uom_id', store=True)
    
    # Values
    actual_qty = fields.Float('Actual Quantity', tracking=True)
    
    source_type = fields.Selection([
        ('project', 'Project Task'),
        ('manual', 'Manual Entry')
    ], required=True, default='project')
    
    state = fields.Selection([('draft', 'Draft'), ('locked', 'Locked')], default='draft', tracking=True)
    
    _sql_constraints = [
        ('unique_activity_period', 
            'UNIQUE(company_id, department_id, activity_master_id, fiscal_year, period_month)',
            'Duplicate actual record for this activity/month found.')
    ]
    
    @api.depends('activity_master_id', 'fiscal_year', 'period_month')
    def _compute_name(self):
        for rec in self:
            # FIX: Check .exists() to prevent MissingError on ghost records
            if rec.activity_master_id and rec.activity_master_id.exists():
                act_name = rec.activity_master_id.name
            else:
                act_name = "Unknown Activity"

            rec.name = f"{act_name} - {rec.fiscal_year}/M{rec.period_month}"

    @api.depends('period_month')
    def _compute_quarter(self):
        for rec in self:
            if 1 <= rec.period_month <= 3: rec.period_quarter = 'q1' 
            elif 4 <= rec.period_month <= 6: rec.period_quarter = 'q2'
            elif 7 <= rec.period_month <= 9: rec.period_quarter = 'q3'
            else: rec.period_quarter = 'q4'
    @api.model
    def _update_actuals(self, company, department, master_item, log_date, amount=0.0):
        """
        Real-Time Aggregator:
        1. Identifies the specific Month/Year.
        2. Searches the Project Log table for ALL entries in that month.
        3. Updates this record with the SUM.
        """
        year_str = str(log_date.year)
        month = log_date.month

        # 1. Find the Execution Record for this Month
        record = self.search([
            ('company_id', '=', company.id),
            ('department_id', '=', department.id),
            ('activity_master_id', '=', master_item.id),
            ('fiscal_year', '=', year_str),
            ('period_month', '=', month)
        ], limit=1)

        # Create if doesn't exist
        if not record:
            record = self.create({
                'company_id': company.id,
                'department_id': department.id,
                'activity_master_id': master_item.id,
                'fiscal_year': year_str,
                'period_month': month,
                'actual_qty': 0.0,
                'source_type': 'project'
            })

        if record.state == 'locked':
            # If period is locked, we can't update.
            return 

        # 2. REAL-TIME SUMMATION
        # We define the start and end of the month
        date_start = log_date.replace(day=1)
        date_end = date_start + relativedelta(months=1, days=-1)

        # We search the LOG table (project.task.log.activity)
        # We filter by the Activity Master ID to catch logs from ANY task linked to this activity
        domain = [
            ('date', '>=', date_start),
            ('date', '<=', date_end),
            ('task_id.aop_activity_id.activity_master_id', '=', master_item.id),
            ('task_id.aop_activity_id.plan_id.department_id', '=', department.id),
            # OPTIONAL: Uncomment to only count verified logs
            ('state', '=', 'verified') 
        ]
        
        # 3. CALCULATE AND WRITE
        all_logs = self.env['project.task.log.activity'].search(domain)
        total_qty = sum(all_logs.mapped('quantity'))

        record.write({'actual_qty': total_qty})


# ==========================================
# 2. FINANCIAL EXECUTION ACTUALS (NEW)
# ==========================================
class ExecutionActualFinancial(models.Model):
    _name = 'corporate.execution.financial'
    _description = 'Financial Execution Actual (Source of Truth)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fiscal_year desc, period_month desc'

    name = fields.Char(compute='_compute_name', store=True)

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', required=True, index=True)

    fiscal_year = fields.Char(string='Fiscal Year', required=True, index=True)
    period_month = fields.Integer(required=True, string='Month (1-12)')
    period_quarter = fields.Selection([
        ('q1', 'Q1'), ('q2', 'Q2'), ('q3', 'Q3'), ('q4', 'Q4')
    ], compute='_compute_quarter', store=True)

    # Master Data Link
    item_id = fields.Many2one('corporate.financial.item', required=True, index=True, string='Budget Item')
    category = fields.Selection(related='item_id.category', store=True, string="Category")

    # Values
    actual_amount = fields.Float('Actual Amount', tracking=True)

    # Source Tracking (e.g., from Accounting or Manual)
    source_type = fields.Selection([
        ('account', 'Accounting/GL'),
        ('manual', 'Manual Entry')
    ], required=True, default='manual')

    state = fields.Selection([('draft', 'Draft'), ('locked', 'Locked')], default='draft', tracking=True)

    _sql_constraints = [
        ('unique_financial_period', 
            'UNIQUE(company_id, department_id, item_id, fiscal_year, period_month)',
            'Duplicate actual record for this financial item/month found.')
    ]

    @api.depends('item_id', 'fiscal_year', 'period_month')
    def _compute_name(self):
        for rec in self:
            # FIX: Check .exists() to prevent MissingError on ghost records
            if rec.item_id and rec.item_id.exists():
                item_name = rec.item_id.name
            else:
                item_name = "Unknown Item"

            rec.name = f"{item_name} - {rec.fiscal_year}/M{rec.period_month}"

    @api.depends('period_month')
    def _compute_quarter(self):
        for rec in self:
            if 1 <= rec.period_month <= 3: rec.period_quarter = 'q1' 
            elif 4 <= rec.period_month <= 6: rec.period_quarter = 'q2'
            elif 7 <= rec.period_month <= 9: rec.period_quarter = 'q3'
            else: rec.period_quarter = 'q4'
            
    @api.model
    def _update_actuals(self, company, department, master_item, log_date, amount=0.0):
        year_str = str(log_date.year)
        month = log_date.month
        
        record = self.search([
            ('company_id', '=', company.id),
            ('department_id', '=', department.id),
            ('item_id', '=', master_item.id),
            ('fiscal_year', '=', year_str),
            ('period_month', '=', month)
        ], limit=1)

        if not record:
            record = self.create({
                'company_id': company.id,
                'department_id': department.id,
                'item_id': master_item.id,
                'fiscal_year': year_str,
                'period_month': month,
                'actual_amount': 0.0,
                'source_type': 'manual'
            })

        if record.state == 'locked': return

        # Summation Logic
        date_start = log_date.replace(day=1)
        date_end = date_start + relativedelta(months=1, days=-1)

        domain = [
            ('date', '>=', date_start),
            ('date', '<=', date_end),
            ('task_id.aop_financial_id.item_id', '=', master_item.id),
            ('task_id.aop_financial_id.plan_id.department_id', '=', department.id)
        ]
        
        all_logs = self.env['project.task.log.financial'].search(domain)
        total_amount = sum(all_logs.mapped('amount'))

        record.write({'actual_amount': total_amount})


# ==========================================
# 3. CAPEX EXECUTION ACTUALS (NEW)
# ==========================================
class ExecutionActualCapex(models.Model):
    _name = 'corporate.execution.capex'
    _description = 'Capex Execution Actual (Source of Truth)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fiscal_year desc, period_month desc'

    name = fields.Char(compute='_compute_name', store=True)

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', required=True, index=True)

    fiscal_year = fields.Char(string='Fiscal Year', required=True, index=True)
    period_month = fields.Integer(required=True, string='Month (1-12)')
    period_quarter = fields.Selection([
        ('q1', 'Q1'), ('q2', 'Q2'), ('q3', 'Q3'), ('q4', 'Q4')
    ], compute='_compute_quarter', store=True)

    # Master Data Link
    capex_item_id = fields.Many2one('corporate.capex.item', required=True, index=True, string='Capex Item')

    # Values (Capex has both Quantity and Cost)
    actual_qty = fields.Float('Actual Qty', tracking=True)
    actual_cost = fields.Float('Actual Cost', tracking=True)

    # Source Tracking (e.g., Purchase Orders or Asset Module)
    source_type = fields.Selection([
        ('purchase', 'Purchase/Asset'),
        ('manual', 'Manual Entry')
    ], required=True, default='manual')

    state = fields.Selection([('draft', 'Draft'), ('locked', 'Locked')], default='draft', tracking=True)

    _sql_constraints = [
        ('unique_capex_period', 
            'UNIQUE(company_id, department_id, capex_item_id, fiscal_year, period_month)',
            'Duplicate actual record for this capex/month found.')
    ]

    @api.depends('capex_item_id', 'fiscal_year', 'period_month')
    def _compute_name(self):
        for rec in self:
            # FIX: Check .exists() to prevent MissingError on ghost records
            if rec.capex_item_id and rec.capex_item_id.exists():
                capex_name = rec.capex_item_id.name
            else:
                capex_name = "Unknown Capex Item"

            rec.name = f"{capex_name} - {rec.fiscal_year}/M{rec.period_month}"

    @api.depends('period_month')
    def _compute_quarter(self):
        for rec in self:
            if 1 <= rec.period_month <= 3: rec.period_quarter = 'q1' 
            elif 4 <= rec.period_month <= 6: rec.period_quarter = 'q2'
            elif 7 <= rec.period_month <= 9: rec.period_quarter = 'q3'
            else: rec.period_quarter = 'q4'
    @api.model
    def _update_actuals(self, company, department, master_item, log_date, qty=0.0, cost=0.0):
        year_str = str(log_date.year)
        month = log_date.month
        
        record = self.search([
            ('company_id', '=', company.id),
            ('department_id', '=', department.id),
            ('capex_item_id', '=', master_item.id),
            ('fiscal_year', '=', year_str),
            ('period_month', '=', month)
        ], limit=1)

        if not record:
            record = self.create({
                'company_id': company.id,
                'department_id': department.id,
                'capex_item_id': master_item.id,
                'fiscal_year': year_str,
                'period_month': month,
                'actual_qty': 0.0,
                'actual_cost': 0.0,
                'source_type': 'manual'
            })

        if record.state == 'locked': return

        # Summation Logic
        date_start = log_date.replace(day=1)
        date_end = date_start + relativedelta(months=1, days=-1)

        domain = [
            ('date', '>=', date_start),
            ('date', '<=', date_end),
            ('task_id.aop_capex_id.capex_item_id', '=', master_item.id),
            ('task_id.aop_capex_id.plan_id.department_id', '=', department.id)
        ]
        
        all_logs = self.env['project.task.log.capex'].search(domain)
        
        total_qty = sum(all_logs.mapped('qty'))
        total_cost = sum(all_logs.mapped('cost'))

        record.write({
            'actual_qty': total_qty,
            'actual_cost': total_cost
        })
# ==========================================
# 4. OKR EXECUTION ACTUALS (Ensure this is added)
# ==========================================
class ExecutionActualOKR(models.Model):
    _name = 'corporate.execution.okr'
    _description = 'OKR Execution Actual'
    _inherit = ['mail.thread']
    _order = 'fiscal_year desc, period_month desc'
    
    name = fields.Char(compute='_compute_name', store=True)
    
    # We use related fields to okr_line_id to populate these
    okr_line_id = fields.Many2one('corporate.performance.okr.line', required=True, index=True, string='Key Result')
    employee_id = fields.Many2one(related='okr_line_id.employee_id', store=True)
    department_id = fields.Many2one(related='okr_line_id.department_id', store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    fiscal_year = fields.Char(required=True, index=True)
    period_month = fields.Integer(required=True)
    period_quarter = fields.Selection([
        ('q1', 'Q1'), ('q2', 'Q2'), ('q3', 'Q3'), ('q4', 'Q4')
    ], compute='_compute_quarter', store=True)
    
    actual_result = fields.Float('Actual Result %', group_operator="avg") # Avg because it is %
    
    state = fields.Selection([('draft', 'Draft'), ('locked', 'Locked')], default='draft')

    @api.depends('okr_line_id', 'fiscal_year', 'period_month')
    def _compute_name(self):
        for rec in self:
            rec.name = f"OKR: {rec.okr_line_id.key_result} - {rec.fiscal_year}/M{rec.period_month}"

    @api.depends('period_month')
    def _compute_quarter(self):
        for rec in self:
            if 1 <= rec.period_month <= 3: rec.period_quarter = 'q1' 
            elif 4 <= rec.period_month <= 6: rec.period_quarter = 'q2'
            elif 7 <= rec.period_month <= 9: rec.period_quarter = 'q3'
            else: rec.period_quarter = 'q4'