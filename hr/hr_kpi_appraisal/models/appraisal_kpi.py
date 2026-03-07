from collections import defaultdict
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AppraisalKpi(models.Model):
    _name = 'appraisal.kpi'
    _description = 'Appraisal Key Performance Indicator'

    name = fields.Char(string='KPI', required=True, help="The Key Performance Indicator name.")
    objective = fields.Html(string='Objective', help="The goal or objective of this KPI.")
    output = fields.Html(string='Expected Output', help="The measurable output expected for this KPI.")
    weight = fields.Float(string='Weight (%)', help="The importance of this KPI in the overall evaluation.")
    Kpi_category = fields.Many2one('appraisal.kpi.category', string='Category', help="The category of this KPI.")
    
    # These fields determine the scope of the KPI
    department_id = fields.Many2one(    
        'hr.department',
        string='Department',
        help="Leave empty if this KPI is general for all departments. This field is set automatically if an employee is chosen."
    )
    user_department_id = fields.Many2one('hr.department', compute='_compute_user_department')
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        help="Leave empty if this KPI applies to a whole department or is general."
    )
    kpi_type = fields.Char(string='KPI Type', compute='_compute_kpi_type', store=True)

    @api.depends('employee_id')
    def _compute_user_department(self):
        for kpi in self:
            if self.env.user.employee_id:
                kpi.user_department_id = self.env.user.employee_id.department_id

    @api.depends('department_id', 'employee_id')
    def _compute_kpi_type(self):
        """Computes the type of the KPI based on its assigned scope."""
        for kpi in self:
            if kpi.employee_id:
                kpi.kpi_type = 'Employee Level'
            elif kpi.department_id:
                kpi.kpi_type = 'Department Level'
            else:
                kpi.kpi_type = 'General Level'

    # --- NEW: Onchange method for Employee/Department relationship ---
    @api.onchange('employee_id')
    def _onchange_employee_id_set_department(self):
        """
        Automatically sets the department based on the selected employee
        to prevent data inconsistencies.
        """
        if self.employee_id and self.employee_id.department_id:
            self.department_id = self.employee_id.department_id
        # Note: To make the department field read-only in the UI when an employee is set,
        # you should add this attribute to the field in your XML view:
        # attrs="{'readonly': [('employee_id', '!=', False)]}"
    
    @api.onchange('department_id')
    def _onchange_department_id_filter_employee(self):
        """
        When the department changes, clear the employee if it no longer matches.
        Also, returns a dynamic domain to filter the employee list.
        """
        # If the currently selected employee is not in the new department, clear it.
        if self.employee_id and self.employee_id.department_id != self.department_id:
            self.employee_id = False

        # If a department is set, filter employees by that department.
        if self.department_id:
            return {'domain': {'employee_id': [('department_id', '=', self.department_id.id)]}}
        else:
            # If no department is set, show all employees.
            return {'domain': {'employee_id': []}}

    @api.constrains('weight')
    def _check_weight_not_below_zero(self):
        """Ensure that the weight of the KPI is not negative."""
        for kpi in self:
            if kpi.weight < 0:
                raise ValidationError(_("KPI weight cannot be negative."))

    @api.constrains('weight', 'department_id', 'employee_id')
    def _check_total_weight(self):
        """
        Validates that the cumulative weight of KPIs does not exceed 100%
        by correctly summing up the hierarchy for all affected scopes.
        This method is designed to be performant for batch operations.
        """
        if not self:
            return

        # Step 1: Efficiently fetch existing weights from the database using read_group.
        # We exclude the records currently being validated ('self') to get a clean baseline.
        kpi_model = self.env['appraisal.kpi']
        domain_others = [('id', 'not in', self.ids)]

        # Get total weight of all other General KPIs
        rg_general = kpi_model.read_group(
            domain_others + [('department_id', '=', False), ('employee_id', '=', False)],
            ['weight'], []
        )
        projected_general_weight = rg_general[0]['weight'] if rg_general and rg_general[0]['weight'] else 0.0

        # Get total weights for each Department
        rg_depts = kpi_model.read_group(
            domain_others + [('department_id', '!=', False), ('employee_id', '=', False)],
            ['weight', 'department_id'], ['department_id']
        )
        projected_dept_weights = defaultdict(float, {
            res['department_id'][0]: res['weight'] for res in rg_depts
        })

        # Get total weights for each Employee
        rg_emps = kpi_model.read_group(
            domain_others + [('employee_id', '!=', False)],
            ['weight', 'employee_id'], ['employee_id']
        )
        projected_emp_weights = defaultdict(float, {
            res['employee_id'][0]: res['weight'] for res in rg_emps
        })

        # Step 2: Add the weights from the records being saved ('self') to our projected totals.
        # This simulates the state of the database *after* the save.
        # We also collect all affected departments and employees to check them later.
        all_affected_depts = set(projected_dept_weights.keys())
        all_affected_emps = set(projected_emp_weights.keys())

        for kpi in self:
            if kpi.employee_id:
                projected_emp_weights[kpi.employee_id.id] += kpi.weight
                all_affected_emps.add(kpi.employee_id.id)
                if kpi.department_id: # An employee must have a department
                     all_affected_depts.add(kpi.department_id.id)
            elif kpi.department_id:
                projected_dept_weights[kpi.department_id.id] += kpi.weight
                all_affected_depts.add(kpi.department_id.id)
            else:
                projected_general_weight += kpi.weight

        # Step 3: Perform the hierarchical validation using the final projected weights.

        # 3.1: Validate General Level
        if projected_general_weight > 100.001:
            raise ValidationError(_(
                "Save Failed: The total weight for all General KPIs cannot exceed 100%%. "
                "Projected total is %(weight)s%%.",
                weight=round(projected_general_weight, 2)
            ))

        # 3.2: Validate all affected Department Levels
        if all_affected_depts:
            depts = self.env['hr.department'].browse(list(all_affected_depts))
            for dept in depts:
                total_dept_level_weight = projected_general_weight + projected_dept_weights[dept.id]
                if total_dept_level_weight > 100.001:
                    raise ValidationError(_(
                        "Save Failed for Department '%(dept)s': The combined weight of General and Department-specific KPIs cannot exceed 100%%. "
                        "Projected total for this department is %(weight)s%%.",
                        dept=dept.name,
                        weight=round(total_dept_level_weight, 2)
                    ))

        # 3.3: Validate all affected Employee Levels
        if all_affected_emps:
            employees = self.env['hr.employee'].browse(list(all_affected_emps))
            for emp in employees:
                dept_id = emp.department_id.id if emp.department_id else None
                total_emp_level_weight = (
                    projected_general_weight + 
                    projected_dept_weights[dept_id] + 
                    projected_emp_weights[emp.id]
                )
                if total_emp_level_weight > 100.001:
                    raise ValidationError(_(
                        "Save Failed for Employee '%(emp)s': The combined weight of General, Department, and Employee-specific KPIs cannot exceed 100%%. "
                        "Projected total for this employee is %(weight)s%%.",
                        emp=emp.name,
                        weight=round(total_emp_level_weight, 2)
                    ))

