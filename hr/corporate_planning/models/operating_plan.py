# -*- coding: utf-8 -*-
from odoo import models, fields, api

# --- HELPER MODEL: QUARTERS ---
class CorporateQuarter(models.Model):
    _name = 'corporate.quarter'
    _description = 'Quarter Configuration'
    
    name = fields.Char(string='Quarter Name', required=True)
    code = fields.Char(string='Code', required=True) # Q1, Q2, Q3, Q4


# --- MAIN MODEL: OPERATING PLAN ---
class CorporateOperatingPlan(models.Model):
    _name = 'corporate.operating.plan'
    _description = 'Annual Operating Plan (AOP)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Plan Title', required=True, default='New Annual Operating Plan')
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    fiscal_year = fields.Char(string='Fiscal Year', required=True, help="e.g. 2018 E.C / 2026 G.C")
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    # --- RELATIONS TO THE 4 ANNEXES ---
    # Renamed to op_activity_ids to avoid conflict with mail.activity.mixin
    op_activity_ids = fields.One2many('corporate.operating.activity', 'plan_id', string='Activity Plan')
    financial_ids = fields.One2many('corporate.operating.financial', 'plan_id', string='Financial Plan')
    kpi_ids = fields.One2many('corporate.operating.kpi.line', 'plan_id', string='KPI Plan')
    capex_ids = fields.One2many('corporate.operating.capex', 'plan_id', string='Capex Plan')
    
    # --- PREVIOUS YEAR LINK ---
    previous_plan_id = fields.Many2one(
        'corporate.operating.plan', 
        string='Previous Year Plan',
        domain="[('department_id', '=', department_id)]",
        help="Link the Annual Plan from the previous fiscal year here to enable historical data fetching in reports."
    )

    # --- UI LOGIC: QUARTER SELECTION ---
    visible_quarter_ids = fields.Many2many(
        'corporate.quarter', 
        string='Display Quarters',
        help="Select which quarters to display in the tables below."
    )

    # Computed Booleans for XML 'column_invisible' logic
    show_q1 = fields.Boolean(compute='_compute_quarter_visibility')
    show_q2 = fields.Boolean(compute='_compute_quarter_visibility')
    show_q3 = fields.Boolean(compute='_compute_quarter_visibility')
    show_q4 = fields.Boolean(compute='_compute_quarter_visibility')

    @api.depends('visible_quarter_ids')
    def _compute_quarter_visibility(self):
        for plan in self:
            selected_codes = plan.visible_quarter_ids.mapped('code')
            plan.show_q1 = 'Q1' in selected_codes
            plan.show_q2 = 'Q2' in selected_codes
            plan.show_q3 = 'Q3' in selected_codes
            plan.show_q4 = 'Q4' in selected_codes

    # --- WORKFLOW ACTIONS ---
    def action_submit(self):
        self.write({'state': 'submitted'})
    def action_approve(self):
        self.write({'state': 'approved'})
    def action_reset(self):
        self.write({'state': 'draft'})

    
    def write(self, vals):
        # Check if we should skip to prevent infinite loops
        if self.env.context.get('skip_resequence'):
            return super(CorporateOperatingPlan, self).write(vals)

        res = super(CorporateOperatingPlan, self).write(vals)
        
        # If financial lines were touched, trigger calculation
        if 'financial_ids' in vals:
            self._resequence_financial_lines()
        return res

    # --- 2. Override Create ---
    @api.model
    def create(self, vals):
        record = super(CorporateOperatingPlan, self).create(vals)
        if 'financial_ids' in vals:
            record._resequence_financial_lines()
        return record

    # --- 3. The Logic (Delete All Totals -> Re-Calculate -> Create New Totals) ---
    def _resequence_financial_lines(self):
        # PREVENT RECURSION: Add context flag
        for plan in self.with_context(skip_resequence=True):
            
            # A. DELETE EXISTING SYSTEM ROWS
            # We delete all rows marked 'is_total' to ensure a clean slate. 
            # This fixes the duplicate issue 100%.
            system_lines = plan.financial_ids.filtered(lambda l: l.is_total)
            system_lines.unlink()

            # Define Order
            category_order = ['revenue', 'cos', 'opex', 'other']
            current_seq = 10
            
            # Initialize Sums
            # Structure: {'annual': 0.0, 'm1': 0.0 ... 'm12': 0.0}
            cat_totals = {cat: {f'm{i}': 0.0 for i in range(1, 13)} for cat in category_order}
            for cat in category_order:
                cat_totals[cat]['annual'] = 0.0

            # B. PROCESS CATEGORIES
            # Fetch only user-entered data lines (ignore sections for math)
            data_lines = plan.financial_ids.filtered(lambda l: not l.is_section and not l.is_total)

            for cat in category_order:
                # 1. Update Section Header Sequence
                header = plan.financial_ids.filtered(lambda l: l.is_section and l.category == cat)
                if header:
                    header.write({'sequence': current_seq})
                    current_seq += 1

                # 2. Process Data Lines for this Category
                cat_items = data_lines.filtered(lambda l: l.category == cat)
                
                # Sort items alphabetically (optional)
                cat_items = cat_items.sorted(key=lambda r: r.item_id.name or '')

                for item in cat_items:
                    item.write({'sequence': current_seq})
                    current_seq += 1
                    
                    # Add to Totals
                    cat_totals[cat]['annual'] += item.annual_budget
                    for i in range(1, 13):
                        cat_totals[cat][f'm{i}'] += getattr(item, f'm{i}')

                # 3. CREATE TOTAL LINE (If there is data or a header)
                # Only create total if there are items or a header exists for this category
                if cat_items or header:
                    label_map = {
                        'revenue': 'TOTAL REVENUE', 
                        'cos': 'TOTAL COST OF SALES', 
                        'opex': 'TOTAL OPERATING EXPENSES', 
                        'other': 'TOTAL OTHER INCOME/EXP'
                    }
                    
                    total_vals = {
                        'plan_id': plan.id,
                        'name': label_map.get(cat),
                        'category': cat,
                        'is_total': True,
                        'is_section': False,
                        'sequence': current_seq,
                        'annual_budget': cat_totals[cat]['annual'],
                    }
                    # Add monthly values
                    for i in range(1, 13):
                        total_vals[f'm{i}'] = cat_totals[cat][f'm{i}']

                    self.env['corporate.operating.financial'].create(total_vals)
                    current_seq += 1

            # C. CALCULATE NET PROFIT
            # Revenue - COS - Opex + Other
            net_vals = {
                'plan_id': plan.id,
                'name': 'NET PROFIT / (LOSS)',
                'is_total': True,
                'is_section': False,
                'category': False, # No category puts it at the end usually
                'sequence': 9999,
            }
            
            # Annual Net
            net_vals['annual_budget'] = (
                cat_totals['revenue']['annual'] - 
                cat_totals['cos']['annual'] - 
                cat_totals['opex']['annual'] + 
                cat_totals['other']['annual']
            )

            # Monthly Net
            for i in range(1, 13):
                m = f'm{i}'
                net_vals[m] = (
                    cat_totals['revenue'][m] - 
                    cat_totals['cos'][m] - 
                    cat_totals['opex'][m] + 
                    cat_totals['other'][m]
                )

            # Create Net Profit Line
            self.env['corporate.operating.financial'].create(net_vals)
    
    

# --- ANNEX 1: ACTIVITY PLAN ---
class OperatingActivity(models.Model):
    _name = 'corporate.operating.activity'
    _description = 'AOP Activity Line'

    plan_id = fields.Many2one('corporate.operating.plan', string='Plan')
    sequence = fields.Integer(default=10)

    activity_master_id = fields.Many2one(
            'corporate.activity.master', 
            string='Objective / Activity', 
            required=True,
            domain="[('department_id', '=', parent.department_id)]"
        )
    uom_id = fields.Many2one('uom.uom', string='UOM')
    annual_target = fields.Float(string='Annual Target')
    okr_line_id = fields.Many2one(
        'corporate.performance.okr.line', 
        string='Linked Key Result',
        domain="[('department_id', '=', parent.department_id)]"
    )
    
    task_id = fields.Many2one('project.task', string="Execution Task", readonly=True)    
    # Monthly Breakdown
    m1 = fields.Float(string='July')
    m2 = fields.Float(string='Aug')
    m3 = fields.Float(string='Sept')
    m4 = fields.Float(string='Oct')
    m5 = fields.Float(string='Nov')
    m6 = fields.Float(string='Dec')
    m7 = fields.Float(string='Jan')
    m8 = fields.Float(string='Feb')
    m9 = fields.Float(string='Mar')
    m10 = fields.Float(string='Apr')
    m11 = fields.Float(string='May')
    m12 = fields.Float(string='Jun')

    responsible_person = fields.Char(string='Executive Body/Person')
    remarks = fields.Char(string='Remarks')
    
    @api.onchange('activity_master_id')
    def _onchange_master(self):
        if self.activity_master_id and self.activity_master_id.uom_id:
            self.uom_id = self.activity_master_id.uom_id
    @api.onchange('m1','m2','m3','m4','m5','m6','m7','m8','m9','m10','m11','m12')
    def _onchange_months(self):
        self.annual_target = sum([self.m1, self.m2, self.m3, self.m4, self.m5, self.m6, 
                                  self.m7, self.m8, self.m9, self.m10, self.m11, self.m12])


# --- ANNEX 2: FINANCIAL PLAN ---
class OperatingFinancial(models.Model):
    _name = 'corporate.operating.financial'
    _description = 'AOP Financial Line'

    plan_id = fields.Many2one('corporate.operating.plan', string='Plan')
    sequence = fields.Integer(default=10)

    # category = fields.Selection([
    #     ('revenue', 'Revenue'),
    #     ('cos', 'Cost of Sales'),
    #     ('opex', 'Operating Expenses (HR & GS)'),
    #     ('other', 'Other Income/Expense')
    # ], string='Category', required=True)
    
    category = fields.Selection(
        related='item_id.category', 
        store=True, 
        readonly=False, # Allow manual override if needed, mostly for Sections
        string='Category'
    )
    
    display_type = fields.Selection([
        ('line_note', 'Note')
    ], default=False, help="Technical field for UX purpose.")

    name = fields.Char(string='Section Label') 

    item_id = fields.Many2one(
        'corporate.financial.item', 
        string='Budget Line Item', 
        domain="[('department_id', '=', parent.department_id)]"
    )
    is_section = fields.Boolean(default=False)
    uom_id = fields.Many2one('uom.uom', string='UOM')
    
    annual_budget = fields.Float(string='Annual Budget (ETB)')
    okr_line_id = fields.Many2one(
            'corporate.performance.okr.line', 
            string='Linked Key Result',
            domain="[('department_id', '=', parent.department_id)]"
        )
        
    task_id = fields.Many2one('project.task', string="Execution Task", readonly=True)    
    # Monthly Breakdown
    m1 = fields.Float(string='July')
    m2 = fields.Float(string='Aug')
    m3 = fields.Float(string='Sept')
    m4 = fields.Float(string='Oct')
    m5 = fields.Float(string='Nov')
    m6 = fields.Float(string='Dec')
    m7 = fields.Float(string='Jan')
    m8 = fields.Float(string='Feb')
    m9 = fields.Float(string='Mar')
    m10 = fields.Float(string='Apr')
    m11 = fields.Float(string='May')
    m12 = fields.Float(string='Jun')

    responsible = fields.Char(string='Executive Body')
    remarks = fields.Char(string='Remarks')
    
    is_total = fields.Boolean(default=False, string="Is Total Row")

    # 3. Validation: Prevent manual deletion of total rows (Optional but good safety)
    def unlink(self):
        for record in self:
            if record.is_total:
                # We usually allow deletion via script, but prevent UI deletion if needed.
                # For now, we allow it because the script will recreate it on save.
                pass 
        return super(OperatingFinancial, self).unlink()
    
    @api.onchange('category')
    def _onchange_category(self):
        if self.is_section and self.category:
            selection_list = self._fields['category']._description_selection(self.env)
            
            self.name = dict(selection_list).get(self.category)
    
    @api.onchange('m1','m2','m3','m4','m5','m6','m7','m8','m9','m10','m11','m12')
    def _onchange_months(self):
        self.annual_budget = sum([self.m1, self.m2, self.m3, self.m4, self.m5, self.m6, 
                                  self.m7, self.m8, self.m9, self.m10, self.m11, self.m12])

    @api.onchange('item_id')
    def _onchange_item(self):
        if self.item_id:
            self.category = self.item_id.category

# --- ANNEX 3: KPI PLAN (BSC) ---
class OperatingKPI(models.Model):
    _name = 'corporate.operating.kpi.line'
    _description = 'AOP KPI Line'

    plan_id = fields.Many2one('corporate.operating.plan', string='Plan')
    sequence = fields.Integer(default=10)

    perspective = fields.Selection([
        ('financial', '1. Financial'),
        ('customer', '2. Customer'),
        ('process', '3. Internal Process'),
        ('learning', '4. Learning & Growth')
    ], string='Perspective (BSC)', required=True)


    kpi_id = fields.Many2one(
        'appraisal.kpi', 
        string='KPI', 
        required=True,
        domain="['|', ('department_id', '=', False), ('department_id', '=', parent.department_id)]"
    )
    weight = fields.Float(string='Weight')
    annual_target = fields.Float(string='Annual Target')

    # Monthly Breakdown (Added to allow Quarterly calculation in Report)
    m1 = fields.Float(string='July')
    m2 = fields.Float(string='Aug')
    m3 = fields.Float(string='Sept')
    m4 = fields.Float(string='Oct')
    m5 = fields.Float(string='Nov')
    m6 = fields.Float(string='Dec')
    m7 = fields.Float(string='Jan')
    m8 = fields.Float(string='Feb')
    m9 = fields.Float(string='Mar')
    m10 = fields.Float(string='Apr')
    m11 = fields.Float(string='May')
    m12 = fields.Float(string='Jun')

    responsible = fields.Char(string='Executive Body')
    remarks = fields.Char(string='Remarks')


# --- ANNEX 4: CAPEX PLAN ---
class OperatingCapex(models.Model):
    _name = 'corporate.operating.capex'
    _description = 'AOP Capex Line'

    plan_id = fields.Many2one('corporate.operating.plan', string='Plan')
    sequence = fields.Integer(default=10)

    capex_item_id = fields.Many2one(
        'corporate.capex.item', 
        string='Objective / Asset', 
        required=True,
        domain="[('department_id', '=', parent.department_id)]"
    )
    
    annual_target_qty = fields.Float(string='Annual Target (Qty)')
    annual_budget_etb = fields.Float(string='Annual Budget (ETB)')

    # Quarterly Plan (Quantity)
    q1_qty = fields.Float(string='Q1 Qty')
    q2_qty = fields.Float(string='Q2 Qty')
    q3_qty = fields.Float(string='Q3 Qty')
    q4_qty = fields.Float(string='Q4 Qty')

    # Quarterly Plan (Financial Budget)
    q1_budget = fields.Float(string='Q1 Budget')
    q2_budget = fields.Float(string='Q2 Budget')
    q3_budget = fields.Float(string='Q3 Budget')
    q4_budget = fields.Float(string='Q4 Budget')

    user_department = fields.Char(string='User Departments')
    remark = fields.Char(string='Remark')
    okr_line_id = fields.Many2one(
            'corporate.performance.okr.line', 
            string='Linked Key Result',
            domain="[('department_id', '=', parent.department_id)]"
        )
    
    task_id = fields.Many2one('project.task', string="Execution Task", readonly=True)    
    @api.onchange('q1_budget', 'q2_budget', 'q3_budget', 'q4_budget')
    def _compute_annual_budget(self):
        self.annual_budget_etb = self.q1_budget + self.q2_budget + self.q3_budget + self.q4_budget

    @api.onchange('q1_qty', 'q2_qty', 'q3_qty', 'q4_qty')
    def _compute_annual_qty(self):
        
        self.annual_target_qty = self.q1_qty + self.q2_qty + self.q3_qty + self.q4_qty