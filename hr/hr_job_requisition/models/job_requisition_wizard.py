from odoo import models, fields, api, _
from odoo.exceptions import UserError


class JobRequisitionRejectWizard(models.TransientModel):
    _name = 'hr.job.requisition.reject.wizard'
    _description = 'Job Requisition Reject Wizard'

    requisition_id = fields.Many2one(
        'hr.job.requisition', string='Requisition', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)
    rejected_by = fields.Many2one(
        'res.users', string='Rejected By', readonly=True)

    def action_confirm_reject(self):
        self.ensure_one()
        requisition = self.requisition_id
        user = self.env.user

        can_reject = False
        if requisition.state == 'draft' and user.has_group('hr_job_requisition.hr_job_requisition_group_approve_department'):
            can_reject = True
        elif requisition.state == 'reviewed' and user.has_group('hr_job_requisition.hr_job_requisition_group_approve_gm'):
            can_reject = True
        elif requisition.state == 'approved' and user.has_group('hr_job_requisition.hr_job_requisition_group_authorize'):
            can_reject = True


        if not can_reject:
            raise UserError(
                _("You do not have the permission to reject this requisition in its current state '%s'.") % requisition.state)



        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason.'))

        requisition.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
            'rejected_by': user.id,
        })
        return True
