from odoo import models, fields, api
import re
from odoo.exceptions import ValidationError
from datetime import timedelta

class HrTimeoffPlan(models.Model):
    _name = 'hr.timeoff.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Time Off Plan'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env.user.employee_id, track_visibility="always")
    year = fields.Char(string='Year', required=True, default=lambda self: str(fields.Date.today().year), track_visibility="always")
    start_date = fields.Date(string='Start Date', required=True, track_visibility="always")
    end_date = fields.Date(string='End Date', required=True, track_visibility="always")
    days = fields.Integer(string='Days', compute='_compute_days')
    timeoff_ids = fields.One2many('hr.leave', 'plan_id', string='Time Off Requests')
    timeoff_count = fields.Integer(string='Requested Timeoff', compute='_compute_timeoff_count')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('refused', 'Cancelled'),
    ], string="Status", default="draft", track_visibility="always")
    is_current_employee = fields.Boolean(
        string='Is Current Employee',
        compute='_compute_is_current_employee',
        store=False
    )

    @api.depends('employee_id.user_id')
    def _compute_is_current_employee(self):
        for plan in self:
            plan.is_current_employee = plan.employee_id.user_id == self.env.user

    @api.constrains('year')
    def _check_year(self):
        for plan in self:
            if not re.match(r'^\d{4}$', plan.year):
                raise ValidationError('Year must be a four-digit number (e.g., 2025).')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for plan in self:
            if plan.start_date > plan.end_date:
                raise ValidationError('Start Date must be before End Date.')
            try:
                plan_year = int(plan.year)
                if plan.start_date.year != plan_year or plan.end_date.year != plan_year:
                    raise ValidationError('Dates must be within the plan year (%s).' % plan.year)
            except ValueError:
                raise ValidationError('Plan year must be a valid number.')
            # Check for overlapping plans for the same employee
            overlapping_plans = self.search([
                ('employee_id', '=', plan.employee_id.id),
                ('id', '!=', plan.id),
                ('start_date', '<=', plan.end_date),
                ('end_date', '>=', plan.start_date),
            ])
            if overlapping_plans:
                raise ValidationError('Plans cannot have overlapping dates for the same employee.')

    @api.depends('timeoff_ids')
    def _compute_timeoff_count(self):
        for plan in self:
            plan.timeoff_count = len(plan.timeoff_ids)

    @api.depends('start_date', 'end_date')
    def _compute_days(self):
        for plan in self:
            if plan.start_date and plan.end_date:
                delta = (plan.end_date - plan.start_date).days + 1  # Including both start and end dates
                plan.days = max(delta, 0)  # Avoid negative days if dates are reversed
            else:
                plan.days = 0

    _sql_constraints = [
        ('unique_employee_year', 'UNIQUE(employee_id, year)', 'Each employee can have only one plan per year.')
    ]

    def action_submit_timeoff_plan(self):
        for record in self:
            record.state = 'submitted'

    def action_approve_timeoff_plan(self):
        for record in self:
            if record.state == 'submitted':
                record.state = 'approved'

    def action_reject_timeoff_plan(self):
        for record in self:
            if record.state == 'submitted':
                record.state = 'refused'

    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'

    def action_view_timeoffs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Time Off Requests',
            'res_model': 'hr.leave',
            'view_mode': 'list,form',
            'domain': [('plan_id', '=', self.id)],
            'context': {
                'default_plan_id': self.id,
                'default_employee_id': self.employee_id.id,
                'default_date_from': self.start_date,
                'default_date_to': self.end_date,
            },
        }

    def action_request_timeoff(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Time Off',
            'res_model': 'hr.leave',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_plan_id': self.id,
                'default_employee_id': self.employee_id.id,
                'default_date_from': self.start_date,
                'default_date_to': self.end_date,
            },
        }

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    plan_id = fields.Many2one('hr.timeoff.plan', string='Plan')

    @api.constrains('plan_id', 'date_from', 'date_to')
    def _check_plan_dates(self):
        for leave in self:
            if leave.plan_id:
                if leave.date_from.date() < leave.plan_id.start_date or leave.date_to.date() > leave.plan_id.end_date:
                    raise ValidationError('Time off request dates must be within the plan dates.')