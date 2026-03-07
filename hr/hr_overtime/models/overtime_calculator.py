from odoo import models, fields, api
from datetime import datetime

from odoo.exceptions import ValidationError


class OvertimeCalcualator(models.Model):
    _name = 'overtime.calculator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "employee_id"

    # name = fields.Char( string="Ref")
    start_date = fields.Datetime(
        string="Start Date", tracking=True, required=True,)
    end_date = fields.Datetime(
        string="End Date", tracking=True, required=True,)
    request_id = fields.Many2one(
        'overtime.request', string="Request", tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', string="Employee",
        tracking=True, required=True)
    department_id = fields.Many2one(
        'hr.department', string="Department", related="employee_id.department_id", required=True)
    # manager_id = fields.Many2one('hr.employee', string="Manager",related="employee_id.partner_id")
    approved_date = fields.Date(string="Approved Date", tracking=True,)
    requested_by = fields.Many2one(
        'hr.employee', string="Requested By", tracking=True,)
    requesting_reason = fields.Html(string="Request Reason")
    rejection_reason = fields.Text(string="Rejection Reason")
    hours = fields.Float(string="Total worked hours", tracking=True,)
    requested_hours = fields.Float(string="Requested hours", tracking=True)
    contract_id = fields.Many2one(
        'hr.contract', string="Contract", related='employee_id.contract_id')
    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('department_approve', 'Review'),
        ('reject', 'Rejected'),
        ('hr_approve', 'HR Approved'),
        ('gm_approve', 'GM Approved'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid')
    ], string="state", default="draft", tracking=True,)
    overtime_type_id = fields.Many2one(
        'overtime.rate', string="Overtime type", tracking=True,)

    value = fields.Float(
        string='Value', compute="_compute_value", store=True, tracking=True,)
    review_by = fields.Many2one(
        'res.users', string="Review By", tracking=True, )
    approve_by = fields.Many2one(
        'res.users', string="Approve By", tracking=True, )
    reject_by = fields.Many2one(
        'res.users', string="Reject By", tracking=True, )
    paid_by = fields.Many2one('res.users', string="Paid", tracking=True, )

    @api.constrains('hours')
    def validate_hours(self):
        for rec in self:
            hours_diff = (rec.end_date - rec.start_date).total_seconds() / 3600
            if hours_diff < rec.hours:
                raise ValidationError(
                    "Hours must be less then or equal to the total hours between start date and end date")
            if rec.hours <= 0:
                raise ValidationError("Hours must be greater then 0")

    @api.onchange('request_id')
    def patch_data_from_request(self):
        for rec in self:
            if rec.request_id:
                rec.start_date = rec.request_id.start_date
                rec.end_date = rec.request_id.end_date
                rec.requested_by = rec.request_id.requested_by
                rec.requesting_reason = rec.request_id.requesting_reason

    @api.model
    def create(self, vals):
        # Custom logic before calling super (if needed)
        record = super(OvertimeCalcualator, self).create(vals)
        # template = self.env.ref('hr_overtime.overtime_request_email_template_id', raise_if_not_found=False)
        # if template:
        #     template.send_mail(self.id, force_send=True)
        return record

    # @api.onchange('employee_id', 'start_date', 'end_date')
    # def total_worked_hours(self):
    #     for rec in self:
    #         overtimes = self.env['hr.attendance'].search(
    #             [('check_in', '>=', rec.start_date), ('check_out', '<=', rec.end_date), ('employee_id', '=', rec.employee_id.id),('status', '=', 'approved'), ('overtime', '>', 0)])
    #         rec.hours=sum(ot.overtime for ot in overtimes)

    @api.depends('employee_id', 'hours', 'overtime_type_id')
    def _compute_value(self):
        for rec in self:
            if rec.employee_id.contract_id:
                contract = rec.employee_id.contract_id
                type = self.env['overtime.rate'].search(
                    [('id', '=', rec.overtime_type_id.id)])

                salary_per_hour = contract.wage / 240
                rec.value = salary_per_hour * type.rate * rec.hours

            else:
                rec.value = 0.0

    # overtime_line_ids = fields.One2many('overtime.lines', 'overtime_id', string='Overtime')

    def action_submit(self):
        self.state = 'submit'

    def action_dept_approve(self):
        self.state = 'department_approve'
        self.review_by = self.env.user.id

    def action_reject(self):
        self.state = 'reject'
        self.reject_by = self.env.user.id
        # template = self.env.ref('hr_overtime.overtime_rejected_email_template_id', raise_if_not_found=False)
        # if template:
        #     template.send_mail(self.id, force_send=True)

    def action_gm_apprve(self):
        self.state = 'gm_approve'

    def action_paid(self):
        self.paid_by = self.env.user.id
        self.state = 'paid'

    def action_in_payment(self):
        self.state = 'in_payment'
        self.in_payment_by = self.env.user.id

    def action_hr(self):
        self.state = 'hr_approve'
        self.state = 'in_payment'
        self.approve_by = self.env.user.id
        # template = self.env.ref('hr_overtime.overtime_approval_email_template_id', raise_if_not_found=False)
        # if template:
        #     template.send_mail(self.id, force_send=True)


class OvertimeRate(models.Model):
    _name = 'overtime.rate'

    name = fields.Char(string="Overtime type", required=True)
    rate = fields.Float(string="Rate", required=True)

    @api.constrains('rate')
    def validate_rate(self):
        for rec in self:
            if rec.rate <= 0:
                raise ValidationError("rate must be greater then 0")


class WorkingWeek(models.Model):
    _inherit = 'resource.calendar'

    weekly_working_hour = fields.Float(string='Weekly Working Hour')
    # total_hour = fields.Float(string='Total Hour', comute="_get_total")
