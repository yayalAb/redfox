# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BudgetHRPlan(models.Model):
    _name = 'corporate.planning.budget.hr'
    _description = 'Human Resource Budget Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Plan Title', required=True, default='New HR Plan')
    company_id = fields.Many2one('res.company', string='Company', required=True)
    fiscal_year_start = fields.Date(string='Start Date', required=True)
    fiscal_year_end = fields.Date(string='End Date', required=True)
    
    line_ids = fields.One2many('corporate.planning.budget.hr.line', 'plan_id', string='Budget Lines')
    
    total_basic_salary = fields.Float(string='Total Basic Salary', compute='_compute_totals', store=True)
    total_transport = fields.Float(string='Total Transport', compute='_compute_totals', store=True)
    total_pension = fields.Float(string='Total Pension', compute='_compute_totals', store=True)
    total_housing = fields.Float(string='Total Housing', compute='_compute_totals', store=True)
    total_gym = fields.Float(string='Total Gym', compute='_compute_totals', store=True)
    total_medical = fields.Float(string='Total Family Medical', compute='_compute_totals', store=True)
    
    total_monthly_budget = fields.Float(string='Total Monthly Budget', compute='_compute_totals', store=True)
    total_annual_budget = fields.Float(string='Grand Total Annual Budget', compute='_compute_totals', store=True)
    
    manpower_line_ids = fields.One2many('corporate.planning.budget.manpower.line', 'plan_id', string='Manpower Lines')
    
    total_manpower_budget = fields.Float(string='Total Manpower Budget', compute='_compute_manpower_total', store=True)
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account', 
        required=True, # Mandatory for integration
        help="Select the Cost Center to push this budget to."
    )
    linked_budget_id = fields.Many2one(
        'budget.analytic', 
        string='Add to Existing Budget',
        domain="[('company_id', '=', company_id)]",
        help="Select a Master Budget (e.g., 'HR 2026'). If empty, a new Budget will be created."
    )
    grand_total_combined = fields.Float(
        string="Total HR Budget (Existing + Manpower)",
        compute='_compute_grand_total_combined',
        store=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved')
    ], string='Status', default='draft', tracking=True)
    
    @api.model
    def _get_department_domain(self):
        if self.env.user.has_group('odoo_corporate_planning.group_planning_manager'):
            return [] 
        
        user_dept = self.env.user.employee_id.department_id
        if user_dept:
            return [('id', 'child_of', user_dept.id)]
        
        return [('id', '=', -1)]

    department_id = fields.Many2one(
        'hr.department', 
        string='Department', 
        required=True, 
        default=lambda self: self.env.user.employee_id.department_id,
        domain=_get_department_domain
    )
    
    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id and self.department_id.company_id:
            self.company_id = self.department_id.company_id

    
    def action_submit(self):
        self.write({'state': 'confirmed'})

    def action_reset(self):
        self.write({'state': 'draft'})

    def action_approve(self):
        """ 
        Approves the plan and creates/updates the Accounting Budget 
        """
        self.write({'state': 'approved'})
        self._create_analytic_budget()

    def _create_analytic_budget(self):
        # Validation
        if 'budget.analytic' not in self.env or 'budget.line' not in self.env:
            return

        BudgetParent = self.env['budget.analytic']
        BudgetLine = self.env['budget.line']

        for plan in self:
            if not plan.analytic_account_id:
                continue

            # LOGIC: Check if we append to existing or create new
            if plan.linked_budget_id:
                budget_id = plan.linked_budget_id.id
                budget_name = plan.linked_budget_id.name
                action_type = "Updated"
            else:
                # Create New Parent Budget
                parent_vals = {
                    'name': f"{plan.name} ({plan.fiscal_year_start.year})",
                    'date_from': plan.fiscal_year_start,
                    'date_to': plan.fiscal_year_end,
                    'company_id': plan.company_id.id,
                }
                new_budget = BudgetParent.create(parent_vals)
                budget_id = new_budget.id
                budget_name = new_budget.name
                action_type = "Created"

            # Create the Line
            line_vals = {
                'budget_analytic_id': budget_id,       # Link to the chosen/created Parent
                'account_id': plan.analytic_account_id.id, 
                'budget_amount': plan.grand_total_combined,
                'date_from': plan.fiscal_year_start,
                'date_to': plan.fiscal_year_end,
                'company_id': plan.company_id.id,
            }
            
            BudgetLine.create(line_vals)
            
            plan.message_post(body=f"✅ Budget {action_type}: Added {plan.grand_total_combined} to '{budget_name}'")         
    @api.depends('line_ids.basic_salary', 'line_ids.transport_allowance', 
                 'line_ids.pension_11', 'line_ids.housing_allowance',
                 'line_ids.gym_allowance', 'line_ids.family_medical_allowance',
                 'line_ids.total_monthly', 'line_ids.grand_total_annual')
    def _compute_totals(self):
        for plan in self:
            plan.total_basic_salary = sum(line.basic_salary for line in plan.line_ids)
            plan.total_transport = sum(line.transport_allowance for line in plan.line_ids)
            plan.total_pension = sum(line.pension_11 for line in plan.line_ids)
            plan.total_housing = sum(line.housing_allowance for line in plan.line_ids)
            plan.total_gym = sum(line.gym_allowance for line in plan.line_ids)
            plan.total_medical = sum(line.family_medical_allowance for line in plan.line_ids)
            
            plan.total_monthly_budget = sum(line.total_monthly for line in plan.line_ids)
            plan.total_annual_budget = sum(line.grand_total_annual for line in plan.line_ids)
    @api.depends('manpower_line_ids.subtotal_salary')
    def _compute_manpower_total(self):
        for plan in self:
            plan.total_manpower_budget = sum(line.subtotal_salary for line in plan.manpower_line_ids)
            

    # --- 2. TOTAL CALCULATION (Grand Total of Both Tabs) ---


    @api.depends('total_annual_budget', 'total_manpower_budget')
    def _compute_grand_total_combined(self):
        for plan in self:
            plan.grand_total_combined = plan.total_annual_budget + plan.total_manpower_budget


    # --- 4. ACTION FOR WIZARD ---
    def action_open_employee_wizard(self):
        return {
            'name': 'Add Employees',
            'type': 'ir.actions.act_window',
            'res_model': 'corporate.budget.hr.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_plan_id': self.id, 'default_department_id': self.department_id.id}
        }

class BudgetHRPlanLine(models.Model):
    _name = 'corporate.planning.budget.hr.line'
    _description = 'HR Budget Line Item'

    plan_id = fields.Many2one('corporate.planning.budget.hr', string='Plan Reference')
    
    employee_id = fields.Many2one('hr.employee', string='Name of Employee')
    job_title = fields.Char(string='Job Title', related='employee_id.job_title', readonly=True)
    
    basic_salary = fields.Float(string='Basic Salary')
    position_allowance = fields.Float(string='Position/Prof Allowance')
    housing_allowance = fields.Float(string='Housing Allowance')
    gym_allowance = fields.Float(string='Gymnasium Allowance')
    family_medical_allowance = fields.Float(string='Family Medical')
    transport_allowance = fields.Float(string='Trans Allowance')
    overtime_estimated = fields.Float(string='OT Estimate')
    
    pension_11 = fields.Float(string='Pension (11%)', compute='_compute_pension', store=True, readonly=False)
    
    cafeteria_allowance = fields.Float(string='Cafeteria Service')
    phone_allowance = fields.Float(string='Phone Allowance')

    total_monthly = fields.Float(string='Total Monthly Income', compute='_compute_monthly_total', store=True)

    annual_increment = fields.Float(string='Annual Increment')
    life_insurance = fields.Float(string='Life Insurance')
    medical_annual = fields.Float(string='Medical (Annual)')
    holiday_bonus = fields.Float(string='Holiday Bonus')
    travel_allowance = fields.Float(string='Travel Allowance')

    grand_total_annual = fields.Float(string='Grand Total Annual', compute='_compute_grand_total', store=True)

    @api.depends('basic_salary')
    def _compute_pension(self):
        for line in self:
            line.pension_11 = line.basic_salary * 0.11

    @api.depends('basic_salary', 'position_allowance', 'housing_allowance', 
                 'gym_allowance', 'family_medical_allowance', 'transport_allowance', 
                 'overtime_estimated', 'pension_11', 'cafeteria_allowance', 'phone_allowance')
    def _compute_monthly_total(self):
        for line in self:
            line.total_monthly = (
                line.basic_salary + line.position_allowance + line.housing_allowance +
                line.gym_allowance + line.family_medical_allowance + line.transport_allowance +
                line.overtime_estimated + line.pension_11 + line.cafeteria_allowance + 
                line.phone_allowance
            )

    @api.depends('total_monthly', 'annual_increment', 'life_insurance', 
                 'medical_annual', 'holiday_bonus', 'travel_allowance')
    def _compute_grand_total(self):
        for line in self:
            line.grand_total_annual = (line.total_monthly * 12) + \
                                      line.annual_increment + \
                                      line.life_insurance + \
                                      line.medical_annual + \
                                      line.holiday_bonus + \
                                      line.travel_allowance
class BudgetManpowerLine(models.Model):
    _name = 'corporate.planning.budget.manpower.line'
    _description = 'Manpower Budget Line'
    _order = 'sequence, id'

    plan_id = fields.Many2one('corporate.planning.budget.hr', string='HR Plan')
    sequence = fields.Integer(string='S.No', default=10)

    # 1. Job Title (Linking to Job Positions is better than typing manually)
    job_position_id = fields.Many2one('hr.job', string='Job Title', required=True)
    
    # 2. Education Level
    education_level = fields.Char(string='Education Level')
    
    # 3. Work Experience
    work_experience = fields.Char(string='Work Experience')
    
    # 4. Type of Employment
    employment_type = fields.Selection([
        ('permanent', 'Permanent'),
        ('contract', 'Contract'),
        ('project', 'Project-Based'),
        ('internship', 'Internship')
    ], string='Type of Employment', default='permanent')
    
    # 5. Grade
    grade = fields.Char(string='Grade')
    
    # 6. Qty
    quantity = fields.Integer(string='Qty', default=1)
    
    # 7. Salary
    salary = fields.Float(string='Salary')
    
    # Calculated Subtotal (Qty * Salary)
    subtotal_salary = fields.Float(string='Total Cost', compute='_compute_subtotal', store=True)

    # 8. Department (Usually specific to the request, e.g., "Project")
    department_id = fields.Many2one('hr.department', string='Department')

    # 9. Starting Date (Text field to allow notes like "We remind you...")
    starting_date_note = fields.Char(string='Starting Date')

    # 10. Remark
    remark = fields.Char(string='Remark')

    @api.depends('quantity', 'salary')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal_salary = line.quantity * line.salary