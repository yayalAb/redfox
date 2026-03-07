from odoo import models, fields, api

class ResPartner(models.Model):
    """
    Extends the res.partner model to capture additional supplier/vendor registration details,
    trade license data, certifications, and company documentation.

    Fields:
        company_category_type (Selection): The legal structure of the company (e.g., LLC, PLC, etc.).
        product_category_id (Many2one): The main product category associated with the partner.
        trade_license_number (Char): The company's trade license number.
        commencement_date (Date): The start date of the trade license validity.
        expiry_date (Date): The expiration date of the trade license.
        trade_license_doc (Binary): Upload of the trade license document.

        certification_name (Char): The name of a certification held by the company.
        certificate_number (Char): The identification number for the certification.
        certifying_body (Char): The organization that issued the certification.
        certification_award_date (Date): The date the certification was awarded.
        certification_expiry_date (Date): The date the certification expires.

        certificate_of_incorporation_doc (Binary): Upload of the Certificate of Incorporation.
        certificate_of_good_standing_doc (Binary): Upload of the Certificate of Good Standing.
        establishment_card_doc (Binary): Upload of the Establishment Card document.
        vat_tax_certificate_doc (Binary): Upload of the VAT or tax certificate.
        memorandum_of_association_doc (Binary): Upload of the Memorandum of Association.
        identification_of_authorised_person_doc (Binary): Upload of the identification for the authorized person.
        bank_letter_doc (Binary): Upload of the bank letter (typically for financial verification).
        past_2_years_financial_statement_doc (Binary): Upload of the last two years of financial statements.
        other_certification_doc (Binary): Upload of any additional certifications.
        company_stamp (Binary): Image of the company’s official stamp.

        signatory_name (Char): Name of the person signing the forms or documents.
        authorized_signatory_name (Char): Name of the legally authorized signatory.
        date_registration (Datetime): Timestamp for when the partner was registered in the system.

    Purpose:
        - To support detailed supplier onboarding and verification.
        - To ensure regulatory compliance through document collection and certification tracking.
        - To facilitate partner classification and product category tagging for procurement and supplier management workflows.
    """
    _inherit = 'res.partner'

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
    product_category_id = fields.Many2one("product.category", string="Product Category")
    trade_license_number = fields.Char(string='Trade License Number')
    commencement_date = fields.Date(string='Commencement Date')
    expiry_date = fields.Date(string='Expiry Date')
    trade_license_doc = fields.Binary(string='Trade License Document')
    # certification fields
    certification_name = fields.Char(string='Certification')
    certificate_number = fields.Char(string='Certificate Number')
    certifying_body = fields.Char(string='Certifying Body')
    certification_award_date = fields.Date(string='Certification Award Date')
    certification_expiry_date = fields.Date(string='Certification Expiry Date')
    # docs
    certificate_of_incorporation_doc = fields.Binary(string='Certificate of Incorporation Document')
    certificate_of_good_standing_doc = fields.Binary(string='Certificate of Good Standing Document')
    establishment_card_doc = fields.Binary(string='Establishment Card Document')
    vat_tax_certificate_doc = fields.Binary(string='VAT Tax Certificate Document')
    memorandum_of_association_doc = fields.Binary(string='Memorandum of Association Document')
    identification_of_authorised_person_doc = fields.Binary(string='Identification of Authorized Person Document')
    bank_letter_doc = fields.Binary(string='Bank Letter Document')
    past_2_years_financial_statement_doc = fields.Binary(string='Past 2 Years Financial Statement Document')
    other_certification_doc = fields.Binary(string='Other Certification Document')
    company_stamp = fields.Binary(string='Company Stamp')
    # signature fields
    signatory_name = fields.Char(string='Signatory')
    authorized_signatory_name = fields.Char(string='Authorized Signatory')
    date_registration = fields.Datetime(string='Date of Registration')
