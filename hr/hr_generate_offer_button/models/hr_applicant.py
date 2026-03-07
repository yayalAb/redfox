from odoo import models, fields

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    allow_generate_offer = fields.Boolean(
        string="Stage Allows Generate Offer",
        related='stage_id.allow_generate_offer',
        readonly=True,
        store=False 
    )