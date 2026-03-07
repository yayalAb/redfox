from odoo import models, fields, api
from odoo.exceptions import UserError
from ..utils.mail_utils import get_smtp_server_email, get_approver_emails, get_supplier_emails


class PartnerEditRequest(models.TransientModel):
    """
    Transient model to handle supplier profile edit requests.

    This model acts as a temporary staging record where changes to a supplier's (res.partner)
    profile are proposed and reviewed. After approval, these changes are applied to the original
    partner record.

    Inherits:
        - mail.thread: Enables chatter functionality.
        - mail.activity.mixin: Allows scheduling activities.

    Fields:
        partner_id (Many2one): The supplier whose data is being proposed for edit.
        state (Selection): Status of the request (Pending, Approved, Rejected).
        reviewed_by (Many2one): User who reviewed the request.
        review_date (Datetime): Timestamp when the review was performed.
        rejection_reason (Text): Reason provided when a request is rejected.
        image_1920 (Binary): Company logo, pulled from partner.
        Various fields: Mirroring key fields from `res.partner` for editable proposal (e.g., license, certification, docs, signatories).

    Methods:
        - _compute_display_name: Generates a display name for UI display.
        - action_approve: Validates and applies the proposed changes to the partner record.
        - action_open_reject_wizard: Opens a wizard form to input a rejection reason.
    """
    _name = 'partner.edit.request'
    _description = 'Partner Edit Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _transient_max_hours = 24 * 30  # 30 days
    _rec_name = 'display_name'

    # Core fields
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete='cascade')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', required=True)
    reviewed_by = fields.Many2one('res.users', string='Reviewed By')
    image_1920 = fields.Binary(related='partner_id.image_1920', string="Logo")
    review_date = fields.Datetime(string='Review Date')
    rejection_reason = fields.Text(string='Rejection Reason')

    # Editable partner fields
    product_category_id = fields.Many2one("product.category", string="Product Category")
    trade_license_number = fields.Char(string='Trade License Number')
    commencement_date = fields.Date(string='Commencement Date')
    expiry_date = fields.Date(string='Expiry Date')
    street = fields.Char(string='Address')
    phone = fields.Char(string='Phone Number')
    certification_name = fields.Char(string='Certification')
    certificate_number = fields.Char(string='Certificate Number')
    certifying_body = fields.Char(string='Certifying Body')
    certification_award_date = fields.Date(string='Certification Award Date')
    certification_expiry_date = fields.Date(string='Certification Expiry Date')
    signatory_name = fields.Char(string='Signatory')
    authorized_signatory_name = fields.Char(string='Authorized Signatory')

    # Editable document fields
    trade_license_doc = fields.Binary(string='Trade License Document')
    trade_license_doc_filename = fields.Char(string='Trade License Document Filename')
    certificate_of_incorporation_doc = fields.Binary(string='Certificate of Incorporation Document')
    certificate_of_incorporation_doc_filename = fields.Char(string='Certificate of Incorporation Document Filename')
    certificate_of_good_standing_doc = fields.Binary(string='Certificate of Good Standing Document')
    certificate_of_good_standing_doc_filename = fields.Char(string='Certificate of Good Standing Document Filename')
    establishment_card_doc = fields.Binary(string='Establishment Card Document')
    establishment_card_doc_filename = fields.Char(string='Establishment Card Document Filename')
    vat_tax_certificate_doc = fields.Binary(string='VAT Tax Certificate Document')
    vat_tax_certificate_doc_filename = fields.Char(string='VAT Tax Certificate Document Filename')
    memorandum_of_association_doc = fields.Binary(string='Memorandum of Association Document')
    memorandum_of_association_doc_filename = fields.Char(string='Memorandum of Association Document Filename')
    identification_of_authorised_person_doc = fields.Binary(string='Identification of Authorized Person Document')
    identification_of_authorised_person_doc_filename = fields.Char(string='Identification of Authorized Person Document Filename')
    bank_letter_doc = fields.Binary(string='Bank Letter Document')
    bank_letter_doc_filename = fields.Char(string='Bank Letter Document Filename')
    past_2_years_financial_statement_doc = fields.Binary(string='Past 2 Years Financial Statement Document')
    past_2_years_financial_statement_doc_filename = fields.Char(string='Past 2 Years Financial Statement Document Filename')
    other_certification_doc = fields.Binary(string='Other Certification Document')
    other_certification_doc_filename = fields.Char(string='Other Certification Document Filename')
    company_stamp = fields.Binary(string='Company Stamp')
    company_stamp_filename = fields.Char(string='Company Stamp Filename')

    def _compute_display_name(self):
        """Compute the display name as '<Partner Name>'s Edit Request'."""
        for record in self:
            record.display_name = f"{record.partner_id.name}'s Edit Request"

    def action_approve(self):
        """
        Approve the edit request and update the related partner record.

        This method:
        - Verifies the request is still in 'pending' state.
        - Gathers non-empty fields from the request.
        - Writes them to the associated partner record.
        - Updates state to 'approved', logs reviewer, and sends approval email.
        """
        for record in self:
            if record.state != 'pending':
                raise UserError('Only pending requests can be approved.')

            update_vals = {}
            for field in [
                'trade_license_number', 'commencement_date', 'expiry_date', 'product_category_id',
                'street', 'phone', 'certification_name', 'certificate_number', 'certifying_body',
                'certification_award_date', 'certification_expiry_date', 'signatory_name',
                'authorized_signatory_name', 'trade_license_doc',
                'certificate_of_incorporation_doc', 'certificate_of_good_standing_doc',
                'establishment_card_doc', 'vat_tax_certificate_doc', 'memorandum_of_association_doc',
                'identification_of_authorised_person_doc', 'bank_letter_doc',
                'past_2_years_financial_statement_doc', 'other_certification_doc', 'company_stamp'
            ]:
                if record[field]:
                    update_vals[field] = record[field]

            record.partner_id.sudo().write(update_vals)

            record.write({
                'state': 'approved',
                'reviewed_by': self.env.user.id,
                'review_date': fields.Datetime.now(),
            })

            email_values = {
                'email_from': get_smtp_server_email(self.env),
                'email_to': self.partner_id.email,
                'subject': 'Supplier Edit Request Approved',
            }
            contexts = {
                'company_name': self.partner_id.name,
                'submitted': self.create_date,
                'my_company': self.env.company.name,
            }
            self.env.ref('VendorBid.email_template_edit_profile_approved') \
                .with_context(**contexts) \
                .send_mail(self.id, email_values=email_values)

    def action_open_reject_wizard(self):
        """
        Open a rejection wizard to collect a rejection reason.

        Returns:
            dict: Action to open the rejection wizard form view.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'partner.edit.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }
