from odoo import models, fields, api
from datetime import datetime

from odoo.exceptions import ValidationError


class OvertimeRequest(models.Model):
    _name = 'overtime.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "requested_by"
    requested_by = fields.Many2one(
        'hr.employee', string="Requested By", required=True, tracking=True, )
    requesting_reason = fields.Html(string="Reason")
    start_date = fields.Datetime(
        string="Start Date", tracking=True, required=True)
    end_date = fields.Datetime(
        string="End Date", tracking=True, required=True,)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('review', 'Review'),
        ('reject', 'Rejected'),
        ('approve', 'Approved'),
    ], string="state", default="draft", tracking=True)
    review_by = fields.Many2one(
        'res.users', string="Review By", tracking=True, )
    approve_by = fields.Many2one(
        'res.users', string="Approve By", tracking=True, )
    reject_by = fields.Many2one(
        'res.users', string="Reject By", tracking=True, )
    employee_ids = fields.One2many('overtime.line',
                                   inverse_name='request_id', tracking=True)

    def action_submit(self):
        for rec in self:
            rec.state = "submit"

    def action_review(self):
        for rec in self:
            rec.state = "review"
            rec.review_by = self.env.user.id

    def action_approve(self):
        for rec in self:
            rec.state = "approve"
            rec.approve_by = self.env.user.id

    def action_reject(self):
        for rec in self:
            rec.state = "reject"
            rec.reject_by = self.env.user.id

    @api.model
    def create(self, vals_list):
        resu = super().create(vals_list)
        if len(resu.employee_ids) == 0:
            raise ValidationError("Please Add Employee list")
        return resu

    def write(self, values):
        if 'employee_ids' in values:
            for rec in self:
                if len(values['employee_ids']) == 0:
                    raise ValidationError("Please Add Employee list")
        return super().write(values)


class OvertimeRequestEmployee(models.Model):
    _name = 'overtime.line'
    request_id = fields.Many2one('overtime.request', string="Request")
    employee_id = fields.Many2one(
        'hr.employee', string="Employee", required=True)
    start_date = fields.Datetime(string="Start Date", tracking=True, )
    end_date = fields.Datetime(string="End Date", tracking=True, )
    hours = fields.Float(string="Hours", tracking=True, )
    remark = fields.Char(string="Remark", tracking=True, )

    @api.constrains("start_date", "end_date")
    def check_date(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date > rec.end_date:
                    raise ValidationError(
                        "Start Date must be less than End Date")
