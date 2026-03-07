from ..utils.mail_utils import get_smtp_server_email
from odoo import models, fields, api
import random

class RegistrationOTP(models.TransientModel):
    """
    Transient model to handle OTP (One-Time Password) verification during supplier registration.

    Fields:
        email (Char):
            The email address to which the OTP is sent. Required field for verification.

        otp (Char):
            A randomly generated 6-digit OTP used for email verification. Automatically generated
            when the record is created.

        is_verified (Boolean):
            Indicates whether the entered OTP has been successfully verified.

        company (Many2one):
            The company associated with the current registration session. Defaults to the
            current user's company or the first available company.

        expiry_time (Datetime):
            The expiry time of the OTP, set to 5 minutes from creation. Prevents expired OTPs
            from being used.

    Purpose:
        - To securely verify email ownership during the supplier registration process.
        - To enhance registration workflow with an OTP-based identity validation step.
        - To automatically expire OTPs after a short duration, improving security.
    """
    _name = 'supplies.registration.otp'
    _description = 'Supplies Registration OTP'
    _transient_max_hours = 1

    email = fields.Char(string='Email', required=True)
    otp = fields.Char(
        string='OTP',
        readonly=True,
        default=lambda self: str(random.randint(100000, 999999))
    )
    is_verified = fields.Boolean(string='Is Verified', default=False)
    company = fields.Many2one('res.company', string='Company')
    expiry_time = fields.Datetime(
        string='Expiry Time',
        default=lambda self: fields.Datetime.add(fields.Datetime.now(), minutes=5),
        readonly=True
    )

    def send_otp_email(self):
        """
        Sends the OTP to the specified email address using the configured email template.

        Sets the company to the current user's company if not already set, and dispatches
        the email using the `get_smtp_server_email` utility to retrieve the sender.
        """
        email_values = {
            'email_from': get_smtp_server_email(self.env)
        }
        self.company = self.env.company or self.env['res.company'].sudo().search([], limit=1)
        self.env.ref(
            'VendorBid.email_template_model_bjit_supplies_registration_otp'
        ).send_mail(self.id, force_send=True, email_values=email_values)

    def verify_otp(self):
        """
        Verifies whether the OTP is valid and has not expired.

        Returns:
            bool: True if the OTP is still valid and has not been verified yet, False otherwise.
        """
        if not self.is_verified and self.expiry_time >= fields.Datetime.now():
            self.write({'is_verified': True})
            return True
        return False
