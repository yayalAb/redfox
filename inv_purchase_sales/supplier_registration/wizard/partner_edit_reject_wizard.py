from odoo import models, fields, api
from ..utils.mail_utils import get_smtp_server_email

class PartnerEditRejectWizard(models.TransientModel):
    _name = 'partner.edit.reject.wizard'
    _description = 'Partner Edit Reject Wizard'

    request_id = fields.Many2one('partner.edit.request', string='Edit Request', required=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject(self):
        """Reject the edit request with the provided reason."""
        self.ensure_one()
        self.request_id.write({
            'state': 'rejected',
            'reviewed_by': self.env.user.id,
            'review_date': fields.Datetime.now(),
            'rejection_reason': self.rejection_reason,
        })
        template = self.env.ref('VendorBid.email_template_model_edit_request_rejection').sudo()
        email_values = {
            'email_from': get_smtp_server_email(self.env),
            'email_to': self.request_id.partner_id.email,
            'subject': 'Edit Request Rejection',
        }

        contexts = {
            'company_name': self.env.company.name,
            'reason': self.rejection_reason
        }
        template.with_context(**contexts).send_mail(self.request_id.id, email_values=email_values)
        return {'type': 'ir.actions.act_window_close'}