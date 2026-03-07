from odoo import models, fields

class HrResumeLine(models.Model):
    _inherit = 'hr.resume.line'

    # Standard Odoo pattern for file uploads.
    # The 'attachment=True' is a performance optimization.
    attachment = fields.Binary(
        string="Attachment",
        attachment=True,
        help="Upload any relevant document for this experience (e.g., certificate, reference letter)."
    )
    attachment_name = fields.Char(string="Attachment Filename")