from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class HrPromotion(models.Model):
    _name = 'hr.promotion'

    name = fields.Char(string='Reference', required=True,
                       copy=False, readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one(
        'hr.employee', string='Employees', required=True)
    creator_id = fields.Many2one(
        'res.users', string='Requestor', default=lambda self: self.env.user, readonly=True)
    appraisal_id = fields.Many2one('hr.appraisal', string='Appraisal')
    appraisal_final_rating = fields.Many2one('hr.appraisal.note',
                                             related='appraisal_id.assessment_note',
                                             string="Appraisal Final Rating",
                                             readonly=True,
                                             store=True
                                             )

    reason = fields.Html(string='Promotion Reason', required=True)
    request_date = fields.Date(
        string='Request Date', default=fields.Date.today)
    approval_date = fields.Date(string='Approve Date', readonly=True)
    rejection_reason = fields.Html(string='Rejection Reason')

    promotion_type = fields.Selection(
        [('salary_promotion', 'Salary Promotion'), ('position_promotion',
                                                    'Position Promotion'), ('position_demotion', 'Position Demotion')],
        string='Promotion Type',
        required=True
    )

    new_department_id = fields.Many2one(
        'hr.department', string='New Department')
    new_job_id = fields.Many2one('hr.job', string='New Job Position')

    state = fields.Selection([
        ('draft', 'Draft'), ('in_review', 'In Review'), ('approved', 'Approved'), ('done', 'Applied'), ('rejected', 'Rejected'),],
        string="Status", default='draft')

    # Old Contract Fields (Current Contract)
    old_contract_id = fields.Many2one(
        'hr.contract', string='Current Contract', compute='_compute_old_contract', store=True)
    old_wage = fields.Monetary(
        string='Old Basic Salary', related='old_contract_id.wage', readonly=True)
    old_structure_type_id = fields.Many2one(
        'hr.payroll.structure.type', string='Old Salary Structure Type', related='old_contract_id.structure_type_id', readonly=True)
    old_resource_calendar_id = fields.Many2one(
        'resource.calendar', string='Old Working Schedule', related='old_contract_id.resource_calendar_id', readonly=True)
    old_date_start = fields.Date(
        string='Old Contract Start Date', related='old_contract_id.date_start', readonly=True)
    old_date_end = fields.Date(
        string='Old Contract End Date', related='old_contract_id.date_end', readonly=True)
    old_schedule_pay = fields.Selection([
        ('annually', 'Annually'), ('semi-annually',
                                   'Semi-annually'), ('quarterly', 'Quarterly'),
        ('bi-monthly', 'Bi-monthly'), ('monthly',
                                       'Monthly'), ('semi-monthly', 'Semi-monthly'),
        ('bi-weekly', 'Bi-weekly'), ('weekly', 'Weekly'), ('daily', 'Daily')],
        string='Old Pay Schedule', related='old_contract_id.schedule_pay', readonly=True)
    old_wage_type = fields.Selection([('monthly', 'Fixed Wage'), ('hourly', 'Hourly Wage')],
                                     string='Old Wage Type', related='old_contract_id.wage_type', readonly=True)
    old_hourly_wage = fields.Monetary(
        string='Old Hourly Wage', related='old_contract_id.hourly_wage', readonly=True)
    old_house_rent_allowance = fields.Monetary(
        string='Old House Rent Allowance', related='old_contract_id.house_rent_allowance', readonly=True)
    old_dearness_allowance = fields.Monetary(
        string='Old Dearness Allowance', related='old_contract_id.dearness_allowance', readonly=True)
    old_travel_allowance = fields.Monetary(
        string='Old Travel Allowance', related='old_contract_id.travel_allowance', readonly=True)
    old_meal_allowance = fields.Monetary(
        string='Old Meal Allowance', related='old_contract_id.meal_allowance', readonly=True)
    old_medical_allowance = fields.Monetary(
        string='Old Medical Allowance', related='old_contract_id.medical_allowance', readonly=True)
    old_position_allowance = fields.Monetary(
        string='Old Position Allowance', related='old_contract_id.position_allowance', readonly=True)
    old_transport_home_allowance = fields.Monetary(
        string='Old Transport Home Allowance', related='old_contract_id.transport_home_allowance', readonly=True)
    old_transport_work_allowance = fields.Monetary(
        string='Old Transport Work Allowance', related='old_contract_id.transport_work_allowance', readonly=True)
    old_fuel_allowance = fields.Monetary(
        string='Old Fuel Allowance', related='old_contract_id.fuel_allowance', readonly=True)
    old_professional_allowance = fields.Monetary(
        string='Old Professional Allowance', related='old_contract_id.professional_allowance', readonly=True)
    old_other_allowance = fields.Monetary(
        string='Old Other Allowance', related='old_contract_id.other_allowance', readonly=True)
    old_cash_indemnity_allowance = fields.Monetary(
        string='Old Cash Indemnity Allowance', related='old_contract_id.cash_indemnity_allowance', readonly=True)
    old_apply_cash_indemnity = fields.Boolean(
        string='Old Apply Cash Indemnity', related='old_contract_id.apply_cash_indemnity', readonly=True)
    old_cash_indemnity_start_date = fields.Date(
        string='Old Cash Indemnity Start Date', related='old_contract_id.cash_indemnity_start_date', readonly=True)
    old_company_id = fields.Many2one(
        'res.company', string='Old Company', related='old_contract_id.company_id', readonly=True)
    old_department_id = fields.Many2one(
        'hr.department', string='Old Department', related='employee_id.department_id', readonly=True)
    old_job_id = fields.Many2one(
        'hr.job', string='Old Job Position', related='employee_id.job_id', readonly=True)
    currency_id = fields.Many2one(
        'res.currency', related='old_contract_id.currency_id', readonly=True)

    # New Contract Fields (Promotion Contract)
    new_wage = fields.Monetary(
        string='New Basic Salary', currency_field='currency_id')
    new_structure_type_id = fields.Many2one(
        'hr.payroll.structure.type', string='New Salary Structure Type')
    new_resource_calendar_id = fields.Many2one(
        'resource.calendar', string='New Working Schedule')
    new_date_start = fields.Date(
        string='New Contract Start Date', required=True)
    new_date_end = fields.Date(string='New Contract End Date')
    new_schedule_pay = fields.Selection([
        ('annually', 'Annually'), ('semi-annually',
                                   'Semi-annually'), ('quarterly', 'Quarterly'),
        ('bi-monthly', 'Bi-monthly'), ('monthly',
                                       'Monthly'), ('semi-monthly', 'Semi-monthly'),
        ('bi-weekly', 'Bi-weekly'), ('weekly', 'Weekly'), ('daily', 'Daily')],
        string='New Pay Schedule')
    new_wage_type = fields.Selection(
        [('monthly', 'Fixed Wage'), ('hourly', 'Hourly Wage')], string='New Wage Type', default='monthly')
    new_hourly_wage = fields.Monetary(
        string='New Hourly Wage', currency_field='currency_id')
    new_house_rent_allowance = fields.Monetary(
        string='New House Rent Allowance', currency_field='currency_id')
    new_dearness_allowance = fields.Monetary(
        string='New Dearness Allowance', currency_field='currency_id')
    new_travel_allowance = fields.Monetary(
        string='New Travel Allowance', currency_field='currency_id')
    new_meal_allowance = fields.Monetary(
        string='New Meal Allowance', currency_field='currency_id')
    new_medical_allowance = fields.Monetary(
        string='New Medical Allowance', currency_field='currency_id')
    new_position_allowance = fields.Monetary(
        string='New Position Allowance', currency_field='currency_id')
    new_transport_home_allowance = fields.Monetary(
        string='New Transport Home Allowance', currency_field='currency_id')
    new_transport_work_allowance = fields.Monetary(
        string='New Transport Work Allowance', currency_field='currency_id')
    new_fuel_allowance = fields.Monetary(
        string='New Fuel Allowance', currency_field='currency_id')
    new_professional_allowance = fields.Monetary(
        string='New Professional Allowance', currency_field='currency_id')
    new_other_allowance = fields.Monetary(
        string='New Other Allowance', currency_field='currency_id')
    new_cash_indemnity_allowance = fields.Monetary(
        string='New Cash Indemnity Allowance', currency_field='currency_id')
    new_apply_cash_indemnity = fields.Boolean(
        string='New Apply Cash Indemnity', default=False)
    new_cash_indemnity_start_date = fields.Date(
        string='New Cash Indemnity Start Date')
    new_company_id = fields.Many2one(
        'res.company', string='New Company', related='employee_id.company_id', readonly=True)

    @api.depends('employee_id')
    def _compute_old_contract(self):
        """Load the current active contract for the employee"""
        for record in self:
            if record.employee_id:
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('state', '=', 'open')
                ], limit=1, order='date_start desc')
                record.old_contract_id = contract.id if contract else False
            else:
                record.old_contract_id = False

    def _copy_old_to_new_values(self):
        """Copy old contract values to new contract fields as defaults"""
        if self.old_contract_id:
            contract = self.old_contract_id
            # Basic contract fields
            self.new_wage = contract.wage or 0.0
            self.new_structure_type_id = contract.structure_type_id
            self.new_resource_calendar_id = contract.resource_calendar_id
            self.new_schedule_pay = contract.schedule_pay
            self.new_wage_type = contract.wage_type or 'monthly'
            self.new_hourly_wage = contract.hourly_wage or 0.0
            # Allowances
            self.new_house_rent_allowance = contract.house_rent_allowance or 0.0
            self.new_dearness_allowance = contract.dearness_allowance or 0.0
            self.new_travel_allowance = contract.travel_allowance or 0.0
            self.new_meal_allowance = contract.meal_allowance or 0.0
            self.new_medical_allowance = contract.medical_allowance or 0.0
            self.new_position_allowance = contract.position_allowance or 0.0
            self.new_transport_home_allowance = contract.transport_home_allowance or 0.0
            self.new_transport_work_allowance = contract.transport_work_allowance or 0.0
            self.new_fuel_allowance = contract.fuel_allowance or 0.0
            self.new_professional_allowance = contract.professional_allowance or 0.0
            self.new_other_allowance = contract.other_allowance or 0.0
            # Cash indemnity
            self.new_cash_indemnity_allowance = contract.cash_indemnity_allowance or 0.0
            self.new_apply_cash_indemnity = contract.apply_cash_indemnity or False
            self.new_cash_indemnity_start_date = contract.cash_indemnity_start_date
            # Copy department and job if they exist on employee
            if self.employee_id and self.employee_id.department_id:
                self.new_department_id = self.employee_id.department_id
            if self.employee_id and self.employee_id.job_id:
                self.new_job_id = self.employee_id.job_id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Load current contract data when employee is selected and copy to new fields"""
        if self.employee_id:
            # Trigger computation of old contract fields
            self._compute_old_contract()
            # Copy old values to new fields as defaults
            self._copy_old_to_new_values()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.promotion') or _('New')
        res = super(HrPromotion, self).create(vals)
        # After creation, if employee is set and new values weren't provided, copy old values to new fields
        if res.employee_id:
            # Check if any new_* fields were explicitly set (except department/job which might be set separately)
            new_fields_provided = any(key.startswith('new_') and key not in (
                'new_department_id', 'new_job_id') for key in vals.keys())
            if not new_fields_provided:
                res._compute_old_contract()
                res._copy_old_to_new_values()
        return res

    @api.constrains('new_job_id', 'new_department_id', 'promotion_type')
    def _check_job_in_department(self):
        for record in self:
            if record.promotion_type in ('position_promotion', 'position_demotion') and record.new_job_id and record.new_department_id:

                if record.new_job_id.department_id != record.new_department_id:
                    pass
                    # raise ValidationError(_(
                    #     "Job and Department Mismatch: The job '%(job)s' does not belong to the department '%(dept)s'. "
                    #     "Please select a job that is part of the chosen department."
                    # ))

    def action_submit(self):
        for record in self:
            if record.reason:
                record.write({'state': 'in_review'})
            else:
                raise UserError('Please provide a reason for this request')

    def action_draft(self):
        for record in self:
            record.write({'state': 'draft'})

    def action_approve(self):
        from dateutil.relativedelta import relativedelta

        for record in self:
            if not record.new_date_start:
                raise UserError(
                    _('New Contract Start Date is required to approve the promotion.'))

            record.write(
                {'state': 'approved', 'approval_date': fields.Date.today()})

            # Update employee department and job if position promotion
            if record.promotion_type in ('position_promotion', 'position_demotion'):
                if record.employee_id and record.new_department_id and record.new_job_id:
                    record.employee_id.write({
                        'department_id': record.new_department_id.id,
                        'job_id': record.new_job_id.id,
                    })

            # End the old contract: set date_end to new_date_start - 1 day
            if record.old_contract_id and record.old_contract_id.state == 'open':
                old_end_date = record.new_date_start - relativedelta(days=1)
                record.old_contract_id.write({
                    'date_end': old_end_date,
                    'state': 'close'
                })

            # Create new contract with promotion details
            if record.employee_id and record.new_date_start:
                contract_vals = {
                    'name': _('Contract for %s - Promotion') % record.employee_id.name,
                    'employee_id': record.employee_id.id,
                    'date_start': record.new_date_start,
                    'date_end': record.new_date_end or False,
                    'wage': record.new_wage or 0.0,
                    'structure_type_id': record.new_structure_type_id.id if record.new_structure_type_id else False,
                    'resource_calendar_id': record.new_resource_calendar_id.id if record.new_resource_calendar_id else False,
                    'schedule_pay': record.new_schedule_pay or False,
                    'wage_type': record.new_wage_type or 'monthly',
                    'hourly_wage': record.new_hourly_wage or 0.0,
                    'company_id': record.new_company_id.id if record.new_company_id else record.employee_id.company_id.id,
                    'state': 'draft',  # Will be set to open after creation
                }

                # Add allowance fields if they exist on contract model
                allowance_fields = [
                    'house_rent_allowance', 'dearness_allowance', 'travel_allowance',
                    'meal_allowance', 'medical_allowance', 'position_allowance',
                    'transport_home_allowance', 'transport_work_allowance',
                    'fuel_allowance', 'professional_allowance', 'other_allowance',
                    'cash_indemnity_allowance'
                ]

                for field in allowance_fields:
                    new_field_value = getattr(record, 'new_%s' % field, False)
                    if new_field_value:
                        contract_vals[field] = new_field_value

                # Add cash indemnity fields
                if record.new_apply_cash_indemnity:
                    contract_vals['apply_cash_indemnity'] = True
                    if record.new_cash_indemnity_start_date:
                        contract_vals['cash_indemnity_start_date'] = record.new_cash_indemnity_start_date

                # Add job and department if position promotion
                if record.promotion_type in ('position_promotion', 'position_demotion'):
                    if record.new_job_id:
                        contract_vals['job_id'] = record.new_job_id.id

                # Create the new contract
                new_contract = self.env['hr.contract'].create(contract_vals)

                # Set contract to open state
                new_contract.write({'state': 'open'})

    def action_done(self):
        for record in self:
            record.write({'state': 'done'})
