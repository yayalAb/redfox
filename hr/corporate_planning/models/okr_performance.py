# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging 
_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_result = fields.Float(string='Task Result (%)', default=0.0, help="Actual achievement of this task.")

# --- 1. CONFIGURATION: BSC PERSPECTIVE ---
class BSCSerspective(models.Model):
    _name = 'corporate.bsc.perspective'
    _description = 'Balanced Scorecard Perspective'

    name = fields.Char(string='Perspective Name', required=True, translate=True)
    sequence = fields.Integer(default=10)
    
class CorporateBSCDepartmentWeight(models.Model):
    _name = 'corporate.bsc.department.weight'
    _description = 'Departmental BSC Perspective Weight'
    _rec_name = 'department_id'

    department_id = fields.Many2one('hr.department', string='Department', required=True, store=True)
    bsc_perspective_id = fields.Many2one('corporate.bsc.perspective', string='BSC Perspective', required=True, store=True)
    weight = fields.Float(string='Max Weight (%)', required=True, store=True, help="Total allowable weight for KPIs under this perspective for this department.")

    _sql_constraints = [
        ('dept_perspective_uniq', 'unique(department_id, bsc_perspective_id)', 'A department can only have one weight rule per perspective!')
    ]

# --- 2. OKR HEADER ---
class CorporateOKR(models.Model):
    _name = 'corporate.performance.okr'
    _description = 'Objectives and Key Results (OKR)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # --- HIERARCHY SETTINGS (The Fix) ---
    _parent_store = True 
    _parent_name = 'parent_okr_id' # <--- 1. Tell Odoo the name of your parent field
    
    name = fields.Char(string='OKR Name', compute='_compute_goal_data', store=True, readonly=False)
    weight = fields.Float(string='Goal Weight (%)', compute='_compute_goal_data', store=True, readonly=False)
    
    # Context
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env.user.employee_id)
    
    department_id = fields.Many2one(
        'hr.department', 
        string='Department', 
        required=True,
        store=True
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    supervisor_id = fields.Many2one('hr.employee', string='Supervisor', related='employee_id.parent_id', store=True)
    
    # Strategic Links
    bsc_perspective_id = fields.Many2one('corporate.bsc.perspective', string='BSC Perspective', store=True)
    # kpi_id = fields.Many2one('appraisal.kpi', string='Linked KPI')
    strategic_goal_id = fields.Many2one(
        'corporate.strategy.goal', # Linking to the specific SMART Objective
        string='Linked Strategic Goal',
        required=True,
        # Optional: Filter by company or active strategy document
        
    )
    
    # Hierarchy Fields
    parent_okr_id = fields.Many2one('corporate.performance.okr', string='Parent OKR', ondelete='restrict', domain="[('id', '!=', id)]")
    
    # <--- 2. REQUIRED FIELD for _parent_store to work
    parent_path = fields.Char(index=True, unaccent=False) 
    
    weight = fields.Float(string='Goal Weight (%)', 
            store=True, 
            readonly=False, 
            precompute=True)
    
    # Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved (In Progress)'),
        ('under_execution', 'Under Execution'),
        ('revised', 'Revised/Archived')
    ], string='State', default='draft', tracking=True)

    # Details
    line_ids = fields.One2many('corporate.performance.okr.line', 'okr_id', string='Key Results')
    note = fields.Html(string='Notes')

    # Aggregated Performance
    total_performance = fields.Float(string='Total Performance', compute='_compute_total_performance', store=True)

    # UPDATED: Weight = The weight of this KPI in the BSC Perspective

    # --- 1. AUTO-FILL NAME FROM KPI ---
    # @api.depends('kpi_id')
    # def _compute_kpi_data(self):
    #     for rec in self:
    #         if rec.kpi_id:
    #             rec.name = rec.kpi_id.name
    #             rec.weight = rec.kpi_id.weight     
    #         else:
    #             rec.name = "Unnamed OKR"
    #             rec.weight = 0.0
                
    @api.depends('strategic_goal_id')
    def _compute_goal_data(self):
        for rec in self:
            if rec.strategic_goal_id:
                rec.name = rec.strategic_goal_id.name
                # rec.weight = rec.strategic_goal_id.weight     
            else:
                rec.name = "Unnamed OKR"
                rec.weight = 0.0
        
    # --- 2. VALIDATION: KEY RESULTS vs OKR WEIGHT ---
    @api.constrains('line_ids', 'weight')
    def _check_key_result_weights(self):
        for okr in self:
            total_kr_weight = sum(line.weight for line in okr.line_ids)
            # Allow a small float tolerance (e.g. 0.01)
            if total_kr_weight > okr.weight + 0.01:
                raise ValidationError(
                    f"Configuration Error!\n"
                    f"The sum of Key Results weights ({total_kr_weight}%) cannot exceed the Goal Weight ({okr.weight}%)."
                )
    # --- 3. VALIDATION: DEPARTMENTAL BSC WEIGHT LIMIT ---
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.department_id:
            self.department_id = self.employee_id.department_id

    # 3. ROBUST CONSTRAINT LOGIC
    @api.constrains('weight', 'department_id', 'bsc_perspective_id', 'state')
    def _check_department_bsc_limit(self):
        for okr in self:
            # Skip if critical data is missing or if record is not active
            if not okr.department_id or not okr.bsc_perspective_id or okr.state in ['revised', 'cancel']:
                continue

            # A. Get the Limit Rule
            # We search based on the *Current Form Value* (okr.department_id)
            configs = self.env['corporate.bsc.department.weight'].search([
                ('department_id', '=', okr.department_id.id),
                ('bsc_perspective_id', '=', okr.bsc_perspective_id.id)
            ], limit=1)

            if not configs:
                # If no rule exists, strictly block or allow (User preference)
                # Here we Block to force configuration
                raise ValidationError(
                    f"Configuration Error!\n"
                    f"No weight limit defined for:\n"
                    f"Department: {okr.department_id.name}\n"
                    f"Perspective: {okr.bsc_perspective_id.name}"
                )

            max_allowed = configs.weight

            # B. Calculate "Weight Used by Others"
            # We construct a domain to find EVERYONE ELSE in this bucket
            domain = [
                ('department_id', '=', okr.department_id.id),      # Must match NEW Dept
                ('bsc_perspective_id', '=', okr.bsc_perspective_id.id), # Must match NEW Persp
                ('state', 'not in', ['revised', 'cancel'])
            ]
            
            # CRITICAL: Exclude the current record ID from the database search.
            # If we are editing, 'okr.id' exists. If creating, it might be a NewId.
            if isinstance(okr.id, int):
                domain.append(('id', '!=', okr.id))
            
            # Fetch others
            other_okrs = self.search(domain)
            sum_others = sum(other_okrs.mapped('weight'))

            # C. Calculate Final Total
            # Final = (Others from DB) + (Me from Form)
            final_total = sum_others + okr.weight

            # Debugging Print (Check your Odoo Logs to verify values)
            print(f"DEBUG VALIDATION: Dept={okr.department_id.name}, Limit={max_allowed}, Others={sum_others}, Me={okr.weight}, Final={final_total}")

            if final_total > (max_allowed + 0.01):
                raise ValidationError(
                    f"Department Limit Exceeded!\n"
                    f"Department: {okr.department_id.name}\n"
                    f"Perspective: {okr.bsc_perspective_id.name}\n"
                    f"---------------------------------\n"
                    f"Max Limit: {max_allowed}%\n"
                    f"Used by Others: {sum_others}%\n"
                    f"Current Request: {okr.weight}%\n"
                    f"Total: {final_total}%\n"
                    f"---------------------------------\n"
                    f"You are exceeding the limit by {final_total - max_allowed}%."
                )
    
    
    # --- CYCLIC CHECK ---
    @api.constrains('parent_okr_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise ValidationError('Error! You cannot create recursive OKRs (Circular Reference).')

    # --- WORKFLOW ACTIONS ---
    def action_submit(self):
        self.write({'state': 'review'})

    def action_approve(self):        
        self.write({'state': 'approved'})
    def action_start_execution(self):
        """ 
        1. Validates that AOP is approved (Optional check).
        2. Creates Main Task for Key Results.
        3. Searches AOP for lines linked to this KR.
        4. Creates Subtasks for those AOP lines.
        """
        # 1. Get Project
        project = self.env['project.project'].search([('name', '=', 'Strategic OKR Execution')], limit=1)
        if not project:
            project = self.env['project.project'].create({'name': 'Strategic OKR Execution'})

        for line in self.line_ids:
            # 2. Create Main Parent Task (The Key Result)
            if not line.task_id:
                main_task = self.env['project.task'].create({
                    'name': f"[{self.employee_id.name}] KR: {line.key_result}",
                    'project_id': project.id,
                    'user_ids': [(4, self.employee_id.user_id.id)] if self.employee_id.user_id else [],
                    'description': f"Objective: {line.objective}\nOutcome: {line.expected_outcome}",
                    'date_deadline': fields.Date.today(),
                    'okr_line_id': line.id, # Link back
                })
                line.task_id = main_task.id
            else:
                main_task = line.task_id

            # 3. Search & Create Subtasks from AOP (Activity, Financial, Capex)
            self._create_aop_subtasks(line, main_task, project)
        
        self.write({'state': 'under_execution'})

    def _create_aop_subtasks(self, okr_line, parent_task, project):
        """ Looks for AOP lines linked to this OKR Line and creates subtasks """
        
        # A. Activities
        # We search for activities linked to this OKR line in approved plans
        activities = self.env['corporate.operating.activity'].search([
            ('okr_line_id', '=', okr_line.id),
            ('plan_id.state', '=', 'approved')
        ])
        for act in activities:
            if not act.task_id:
                # FIX 1: Use 'activity_master_id.name' instead of 'objective'
                task_name = f"Activity: {act.activity_master_id.name}" if act.activity_master_id else "Activity Task"
                
                subtask = self.env['project.task'].create({
                    'name': task_name,
                    'project_id': project.id,
                    'parent_id': parent_task.id, 
                    'user_ids': parent_task.user_ids.ids,
                    'aop_activity_id': act.id, 
                    'task_type': 'activity' 
                })
                act.task_id = subtask.id

        # B. Financials
        financials = self.env['corporate.operating.financial'].search([
            ('okr_line_id', '=', okr_line.id),
            ('plan_id.state', '=', 'approved')
        ])
        for fin in financials:
            if not fin.task_id:
                # FIX 2: Use 'item_id.name' instead of 'name' (or fin.name if you kept the label field)
                # In previous steps we agreed fin.name is a label derived from item_id
                # But safer to use the Master Item name directly
                task_name = f"Financial: {fin.item_id.name}" if fin.item_id else "Financial Task"

                subtask = self.env['project.task'].create({
                    'name': task_name,
                    'project_id': project.id,
                    'parent_id': parent_task.id,
                    'user_ids': parent_task.user_ids.ids,
                    'aop_financial_id': fin.id,
                    'task_type': 'financial'
                })
                fin.task_id = subtask.id

        # C. Capex
        capexs = self.env['corporate.operating.capex'].search([
            ('okr_line_id', '=', okr_line.id),
            ('plan_id.state', '=', 'approved')
        ])
        for cap in capexs:
            if not cap.task_id:
                # FIX 3: Use 'capex_item_id.name' instead of 'objective'
                task_name = f"Capex: {cap.capex_item_id.name}" if cap.capex_item_id else "Capex Task"

                subtask = self.env['project.task'].create({
                    'name': task_name,
                    'project_id': project.id,
                    'parent_id': parent_task.id,
                    'user_ids': parent_task.user_ids.ids,
                    'aop_capex_id': cap.id,
                    'task_type': 'capex'
                })
                cap.task_id = subtask.id
    def action_revise(self):
        self.write({'state': 'draft'})

    @api.depends('line_ids.performance_score')
    def _compute_total_performance(self):
        for okr in self:
            okr.total_performance = sum(line.performance_score for line in okr.line_ids)


# --- 3. OKR LINES ---
class CorporateOKRLine(models.Model):
    _name = 'corporate.performance.okr.line'
    _description = 'OKR Key Result Line'
    _rec_name = 'key_result' 


    okr_id = fields.Many2one('corporate.performance.okr', string='OKR')
    
    # Reporting Fields (Stored for Pivot/Graph)
    employee_id = fields.Many2one(related='okr_id.employee_id', store=True)
    department_id = fields.Many2one(related='okr_id.department_id', store=True)
    bsc_perspective_id = fields.Many2one(related='okr_id.bsc_perspective_id', store=True)

    # Columns
    objective = fields.Char(string='Objective', required=True)
    key_result = fields.Char(string='Key Result (Action)', required=True)
    expected_outcome = fields.Char(string='Expected Outcome')
    standard = fields.Char(string='Standard')
    
    weight = fields.Float(string='Weight')
    
    # Integration
    task_id = fields.Many2one('project.task', string='Linked Task', readonly=True)
    
    # Calculation
    actual_result = fields.Float(
        string='Actual Result (%)', 
        compute='_compute_actual_from_task', 
        store=True, 
        readonly=False
    )
    
    performance_score = fields.Float(string='Performance', compute='_compute_performance', store=True)

    # --- AUTO-UPDATE FROM PROJECT ---
    def _get_task_progress(self):
        for line in self:
            if line.task_id:
                if line.task_id.stage_id.fold:
                    line.actual_result = 100.0
                    
    @api.depends('task_id', 'task_id.task_result')
    def _compute_actual_from_task(self):
        for line in self:
            if line.task_id:
                line.actual_result = line.task_id.task_result
            else:
                pass

    @api.depends('weight', 'actual_result')
    def _compute_performance(self):
        for line in self:
            line.performance_score = (line.actual_result / 100.0) * line.weight