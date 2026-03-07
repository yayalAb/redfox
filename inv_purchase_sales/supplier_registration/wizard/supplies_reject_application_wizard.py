from odoo import models, fields, api
from ..utils.mail_utils import get_smtp_server_email

class RejectApplicationWizard(models.TransientModel):
    _name = 'supplies.reject.application.wizard'
    _description = 'Reject Application Wizard'

    reason = fields.Text(string='Reason')
    registration_id = fields.Many2one('supplies.registration', string='Registration')

    def action_reject_application(self):
        self.registration_id.write({'state': 'rejected', 'comments': self.reason})
        template = self.env.ref('VendorBid.email_template_model_supplies_vendor_registration_rejection').sudo()
        email_values = {
            'email_from': get_smtp_server_email(self.env),
            'email_to': self.registration_id.email,
            'subject': 'Registration Rejection',
        }
        contexts = {
            'comany_name': self.env.company.name,
            'reason': self.reason
        }
        template.with_context(**contexts).send_mail(self.registration_id.id, email_values=email_values)
        return {'type': 'ir.actions.act_window_close'}