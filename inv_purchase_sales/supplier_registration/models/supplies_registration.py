from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..utils import schemas
from ..utils import supplier_registration_utils as utils
from ..utils.mail_utils import get_smtp_server_email


class SuppliesRegistrationContact(models.Model):
    """
    Model for storing contact details related to a supplier's registration.
    These include primary, finance, authorized, and client reference contacts.
    """
    _name = 'supplies.contact'
    _description = 'Supplies Registration Contact'

    name = fields.Char(string='Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    address = fields.Char(string='Address')

    @api.model
    def cleanup_dangling_contacts(self):
        """
        Deletes contact records not linked to any registration record.
        Helps prevent orphaned contact data from accumulating.
        """
        all_registrations = self.env['supplies.registration'].search([])
        used_contact_ids = (
            all_registrations.mapped('primary_contact_id').ids +
            all_registrations.mapped('finance_contact_id').ids +
            all_registrations.mapped('authorized_contact_id').ids +
            all_registrations.mapped('client_ref_ids').ids
        )
        dangling_contacts = self.search([('id', 'not in', used_contact_ids)])
        dangling_contacts.unlink()


class SuppliesRegistration(models.TransientModel):
    """
    Transient model for the supplier registration form.
    Stores temporary registration data until the process is finalized.
    """
    _name = 'supplies.registration'
    _description = 'Supplies Registration'
    _transient_max_hours = 24 * 30  # Keep for 30 days

    # -------------------------
    # Registration State
    # -------------------------
    state = fields.Selection(
        [
            ('submitted', 'Submitted'),
            ('rejected', 'Rejected'),
            ('blacklisted', 'Blacklisted'),
            ('approved', 'Approved'),
            ('finalized', 'Finalized'),
        ],
        default='submitted',
        string='Application State',
    )

    # -------------------------
    # Company Information
    # -------------------------
    name = fields.Char(string='Company Name', required=True)
    company_category_type = fields.Selection(
        [
            ('LLC', 'LLC'),
            ('PLC', 'PLC'),
            ('Limited', 'Limited'),
            ('Partnership', 'Partnership'),
            ('Sole Proprietorship', 'Sole Proprietorship'),
            ('Others', 'Others'),
        ]
    )
    product_category_id = fields.Many2one(
        "product.category", string="Product Category")
    image_1920 = fields.Binary(string='Logo')
    company_stamp = fields.Binary(string='Company Stamp')
    email = fields.Char(string='Email', required=True)
    street = fields.Char(string='Address Line 1', required=True)
    street2 = fields.Char(string='Address Line 2')
    trade_license_number = fields.Char(string='Trade License Number')
    vat = fields.Char(string='Tax Identification Number')
    commencement_date = fields.Date(string='Commencement Date')
    supplier_type = fields.Selection(
        [('local', 'Local'),
         ('foreign', 'Foreign')],
        string='Supplier Type',
    )

    # -------------------------
    # Contact Information
    # -------------------------
    primary_contact_id = fields.Many2one(
        'supplies.contact', string='Primary Contact', required=True)
    finance_contact_id = fields.Many2one(
        'supplies.contact', string='Finance Contact')
    authorized_contact_id = fields.Many2one(
        'supplies.contact', string='Authorized Contact')
    client_ref_ids = fields.Many2many(
        'supplies.contact', string='Client References')

    expiry_date = fields.Date(string='Expiry Date')

    # -------------------------
    # Bank Information
    # -------------------------
    bank_name = fields.Char(string='Bank Name')
    swift_code = fields.Char(string='Bank SWIFT Code')
    iban = fields.Char(string='IBAN')
    branch_address = fields.Char(string='Branch Address')
    acc_holder_name = fields.Char(string='Account Name')
    acc_number = fields.Char(string='Account Number')

    # -------------------------
    # Certification
    # -------------------------
    certification_name = fields.Char(string='Certification')
    certificate_number = fields.Char(string='Certificate Number')
    certifying_body = fields.Char(string='Certifying Body')
    certification_award_date = fields.Date(string='Certification Award Date')
    certification_expiry_date = fields.Date(string='Certification Expiry Date')

    # -------------------------
    # Supporting Documents
    # -------------------------
    trade_license_doc = fields.Binary(
        string='Trade License / Business Registration')
    certificate_of_incorporation_doc = fields.Binary(
        string='Certificate of Incorporation')
    certificate_of_good_standing_doc = fields.Binary(
        string='Certificate of Good Standing')
    establishment_card_doc = fields.Binary(string='Establishment Card')
    vat_tax_certificate_doc = fields.Binary(string='VAT / Tax Certificate')
    memorandum_of_association_doc = fields.Binary(
        string='Memorandum of Association')
    identification_of_authorised_person_doc = fields.Binary(
        string='Identification of Authorised Person')
    bank_letter_doc = fields.Binary(
        string='Bank Letter indicating Bank Account Information')
    past_2_years_financial_statement_doc = fields.Binary(
        string='Past 2 Years of Financial Statement')
    other_certification_doc = fields.Binary(
        string='Other Certification / Accreditation')

    # -------------------------
    # Signature and Comments
    # -------------------------
    signatory_name = fields.Char(string='Signatory')
    authorized_signatory_name = fields.Char(string='Authorized Signatory')
    comments = fields.Text(string='Comments')

    # -------------------------
    # Actions
    # -------------------------
    def action_approve(self):
        """
        Approve the registration if it's in the 'submitted' state.
        """
        if self.state == 'submitted':
            return self.write({'state': 'approved'})
        raise ValidationError(
            'Invalid state change. Can only approve submitted applications.')

    def action_finalize(self):
        """
        Finalize the registration process:
        - Validates for duplicate emails/TIN
        - Validates schemas
        - Creates res.partner and res.users
        - Sends confirmation email
        - Moves state to 'finalized'
        """
        if self.state != 'approved':
            raise ValidationError(
                'Invalid state change. Can only finalize approved applications.')

        # Duplicate Check
        existing_company = self.env['res.partner'].sudo().search(
            ['|', ('email', '=', self.email),
             ('vat', '!=', False), ('vat', '=', self.vat)]
        )
        if existing_company:
            raise ValidationError(
                'Company with the same email or TIN already exists.')

        # Schema Validation
        company_schema = schemas.CompanySchema.model_validate(self)
        user_schema = schemas.UserSchema.model_validate(self)

        # Prepare partner data
        company_data = company_schema.model_dump()
        child_ids = utils.get_child_contacts(self)
        company_data['child_ids'] = child_ids

        if self.bank_name and self.acc_number:
            bank_schema = schemas.BankSchema.model_validate(self)
            bank_ids_schema = schemas.BankAccountSchema.model_validate(self)
            bank = utils.get_or_create_bank(self.env, bank_schema.model_dump())
            bank_data = bank_ids_schema.model_dump(bank_id=bank.id)

            company_data['bank_ids'] = [(0, 0, bank_data)]

        # Create partner and user
        company = self.env['res.partner'].sudo().create(company_data)
        user_data = user_schema.model_dump(
            partner_id=company.id,
            company_id=self.env.company.id,
            groups_id=[(6, 0, self.env.ref('base.group_portal').ids)]
        )
        self.env['res.users'].sudo().create(user_data)

        # Send confirmation email
        email_values = {
            'email_from': get_smtp_server_email(self.env),
            'email_to': self.email,
            'subject': 'Supplier Registration Confirmation',
        }
        context = {
            'email': self.email,
            'password': self.email,
        }
        self.env.ref(
            'VendorBid.email_template_model_supplies_vendor_registration_confirmation'
        ).with_context(**context).send_mail(self.id, email_values=email_values)

        return self.write({'state': 'finalized'})

    def action_blacklist(self):
        """
        Open wizard to blacklist the registration.
        """
        wizard = self.env['supplies.blacklist.wizard'].create({
            'email': self.email,
            'registration_id': self.id,
        })
        return {
            'name': 'Blacklist',
            'type': 'ir.actions.act_window',
            'res_model': 'supplies.blacklist.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_reject(self):
        """
        Open wizard to reject the registration.
        """
        wizard = self.env['supplies.reject.application.wizard'].create({
            'registration_id': self.id,
        })
        return {
            'name': 'Reject Application',
            'type': 'ir.actions.act_window',
            'res_model': 'supplies.reject.application.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
