# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    @api.ondelete(at_uninstall=False)
    def _unlink_except_validated_work_entries(self):
        pass
        # if any(w.state == 'validated' for w in self):
        #     raise UserError(
        #         _("This work entry is validated. You can't delete it."))


class JobRequisition(models.Model):
    _name = 'hr.job.requisition'
    _description = 'Job Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Requisition Title',
                       required=True, tracking=True)

    justification = fields.Html(string='Justification', required=True)
    requester_department_id = fields.Many2one(
        'hr.department',
        compute='_compute_requester_department',
        store=False,  # Not necessary to store, it's only for the domain
        string="Requester's Department for Domain"
    )

    requested_by = fields.Many2one(
        'res.users', string='Requested by', default=lambda self: self.env.user, readonly=True)
    # domain="[('id', 'child_of', requester_department_id)]"
    department_id = fields.Many2one(
        'hr.department', string='Department', required=True,
    )

    job_id = fields.Many2one('hr.job', string='Job Position', required=True, domain="[('department_id', '=', department_id)]",
                             help="Select the base job position template.")
    employees_needed = fields.Integer(
        string='Vacancy', default=1, required=True)

    reviewed_by = fields.Many2one(
        'res.users', string='Reviewed By', readonly=True)
    approved_by = fields.Many2one(
        'res.users', string='Approved By', readonly=True)
    authorized_by = fields.Many2one(
        'res.users', string='Authorized By', readonly=True)
    published_by = fields.Many2one(
        'res.users', string='Published By', readonly=True)
    rejected_by = fields.Many2one(
        'res.users', string='Rejected By', readonly=True)

    rejection_reason = fields.Text(string='Rejection Reason')
    approve_date = fields.Datetime(string='Approved On', readonly=True)
    published_date = fields.Datetime(string='Published On', readonly=True)

    job_post_id = fields.Many2one('hr.job', string='Created Job Post', readonly=True,
                                  help="The job post created from this requisition after approval.")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('authorized', 'Authorized'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', readonly=True, tracking=True)

    @api.depends('requested_by')
    def _compute_requester_department(self):
        """Safely computes the department of the requester."""
        for requisition in self:
            if requisition.requested_by and requisition.requested_by.employee_id:
                requisition.requester_department_id = requisition.requested_by.employee_id.department_id
            else:
                requisition.requester_department_id = False

    def action_submit(self):
        if self.env.user.has_group('hr_job_requisition.hr_job_requisition_group_requester'):
            self.write({'state': 'submitted'})
        if self.env.user.has_group('hr_job_requisition.hr_job_requisition_group_approve_department'):
            self.write({'state': 'reviewed', 'reviewed_by': self.env.user.id})
        if self.env.user.has_group('hr_job_requisition.hr_job_requisition_group_approve_gm'):
            self.write({'state': 'approved', 'approved_by': self.env.user.id})
        if (
            self.env.user.has_group(
                'hr_job_requisition.hr_job_requisition_group_authorize')
            or self.env.user.has_group('hr_job_requisition.hr_job_requisition_group_publish')
            or self.env.user.has_group('hr_job_requisition.hr_job_requisition_group_approve_co')
        ):
            self.write(
                {'state': 'authorized', 'authorized_by': self.env.user.id})

    def action_review(self):
        self.write({'state': 'reviewed', 'reviewed_by': self.env.user.id})

    def action_approve(self):
        self.write({'state': 'approved', 'approved_by': self.env.user.id})

    def action_authorize(self):
        self.write({'state': 'authorized', 'authorized_by': self.env.user.id})

    def action_publish(self):
        for requisition in self:
            domain = [
                ('name', '=', requisition.job_id.name),
            ]
            existing_job = self.env['hr.job'].search(domain, limit=1)
            if not existing_job:
                raise UserError(_(
                    "Operation cannot be completed. There is no active job posting for '%s' "
                    "in the '%s'. Please ask HR to create one first."
                ) % (requisition.job_id.name, requisition.department_id.name))

            if requisition.job_id.is_published == True:
                new_employee_count = existing_job.no_of_recruitment + requisition.employees_needed
            else:
                new_employee_count = requisition.employees_needed
            existing_job.write({
                'no_of_recruitment': new_employee_count,
                'is_published': True
            })

            requisition.write({
                'state': 'published',
                'approve_date': fields.Datetime.now(),
                'job_post_id': existing_job.id,
                'published_by': self.env.user.id,
                'published_date': fields.Datetime.now()
            })

        return True

    def action_set_to_draft(self):
        self.write({'state': 'draft', 'rejection_reason': ''})

    @api.onchange('job_id')
    def _onchange_job_id(self):
        """
        When the user selects a Job Position, this method automatically
        fills the Department field based on the department of the selected job.
        """
        if self.job_id and self.job_id.department_id:
            self.department_id = self.job_id.department_id
        else:
            self.department_id = False
