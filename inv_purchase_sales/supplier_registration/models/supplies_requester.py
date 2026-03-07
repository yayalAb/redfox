from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..utils.mail_utils import get_smtp_server_email

class SuppliesRequester(models.Model):
    """
    Model to manage requesters applying for access to the supplies system.

    Fields:
        name (Char): Full name of the requester.
        email (Char): Email address of the requester; used as login for user creation.
        phone (Char): Contact phone number of the requester.
        profile_picture (Image): Optional image uploaded by the requester.
        reason (Text): Reason provided by the requester for applying.
        state (Selection): Current status of the request (Requested, Approved, or Rejected).

    Purpose:
        - To review and manage registration requests from potential requesters.
        - To automate the creation of portal users with appropriate access rights upon approval.
        - To notify users via email whether their request has been approved or rejected.
        - To periodically clean up rejected requests through a scheduled cron job.

    Methods:
        action_approve:
            Approves a requester, creates a corresponding portal user with required groups,
            and sends an approval email.

        action_reject:
            Marks the request as rejected and sends a rejection email.

        _cron_delete_rejected_requesters:
            Cron method that deletes all rejected requester records to maintain database hygiene.
    """
    _name = 'supplies.requester'
    _inherit = ['mail.thread']
    _description = 'Requester'

    name = fields.Char(string='Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    profile_picture = fields.Image()
    reason = fields.Text(string='Reason')
    state = fields.Selection([
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='requested')

    def action_approve(self):
        """
        Approves a requester, creates a user account with portal and requester access,
        and sends a notification email with login credentials.
        """
        portal_group = self.env.ref('base.group_portal')
        requester_group = self.env.ref('VendorBid.group_supplies_requester')

        for rec in self:
            if not rec.email or not rec.phone:
                raise ValidationError(_("Email and phone are required to create a user."))

            # Check if a user already exists with this email
            existing_user = self.env['res.users'].search([('login', '=', rec.email)], limit=1)
            if existing_user:
                raise ValidationError(_("A user with this email already exists."))

            # Create user
            user = self.env['res.users'].sudo().create({
                'name': rec.name,
                'login': rec.email,
                'email': rec.email,
                'password': rec.email,  # Should be changed by the user later
                'active': True,
            })
            user.write({'groups_id': [(5, 0, 0), (4, portal_group.id), (4, requester_group.id)]})

            # Update state to approved
            rec.state = 'approved'
            email_values = {
                'email_from': get_smtp_server_email(self.env),
                'email_to': rec.email,
                'subject': 'Requester Registration Approved',
            }
            contexts = {
                'email': rec.email,
                'password': rec.email,
            }

            template = self.env.ref('VendorBid.email_template_model_supplies_requester_approved').sudo()
            template.with_context(**contexts).sudo().send_mail(rec.id, email_values=email_values)

    def action_reject(self):
        """
        Rejects a requester and sends a rejection email notification.
        """
        self.state = 'rejected'
        email_values = {
            'email_from': get_smtp_server_email(self.env),
            'email_to': self.email,
            'subject': 'Requester Registration Rejected',
        }
        template = self.env.ref('VendorBid.email_template_model_supplies_requester_rejected').sudo()
        template.with_context({}).sudo().send_mail(self.id, email_values=email_values)

    def _cron_delete_rejected_requesters(self):
        """
        Scheduled cron job that deletes all requester records marked as rejected.
        """
        rejected_records = self.search([('state', '=', 'rejected')])
        rejected_records.unlink()
