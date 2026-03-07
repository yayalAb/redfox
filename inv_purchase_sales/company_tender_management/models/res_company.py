from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    # --- Legal Documents ---
    business_license = fields.Binary(string="Business License", attachment=True)
    commercial_registration = fields.Binary(string="Commercial Registration", attachment=True)
    tin_document = fields.Binary(string="TIN Certificate", attachment=True)
    vat_document = fields.Binary(string="VAT Certificate", attachment=True)
    tax_clearance = fields.Binary(string="Tax Clearance", attachment=True)
    egp_registration = fields.Binary(string="EGP Registration", attachment=True)
    vendor_assessment = fields.Binary(string="Vendor Assessment", attachment=True)

    # --- Company Profile Documents ---
    experience_letters = fields.Many2many(
        'ir.attachment', 
        string="Previous Exprience & Testimonials",
    )
    audit_report = fields.Binary(string="Audit Report", attachment=True)
    financial_standing = fields.Binary(string="Financial Standing", attachment=True)

    business_license_filename = fields.Char("Business License Filename")
    commercial_registration_filename = fields.Char("Commercial Registration Filename")
    tin_document_filename = fields.Char("TIN Certificate Filename")
    vat_document_filename = fields.Char("VAT Certificate Filename")
    tax_clearance_filename = fields.Char("Tax Clearance Filename")
    egp_registration_filename = fields.Char("EGP Registration Filename")
    vendor_assessment_filename = fields.Char("Vendor Assessment Filename")

    # Company Profile Documents
    experience_letters_filename = fields.Char("Previous Experience & Testimonials Filename")
    audit_report_filename = fields.Char("Audit Report Filename")
    financial_standing_filename = fields.Char("Financial Standing Filename")