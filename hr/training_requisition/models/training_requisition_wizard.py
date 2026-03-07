from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TrainingRequisitionRejectWizard(models.TransientModel):
    _name = 'training.requisition.reject.wizard'
    _description = 'Training Requisition Reject Wizard'

    requisition_id = fields.Many2one('training.requisition', string='Requisition', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_reject(self):
        self.ensure_one()
        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason.'))
        self.requisition_id.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        return True