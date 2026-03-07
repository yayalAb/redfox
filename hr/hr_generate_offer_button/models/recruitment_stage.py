from odoo import models, fields

class RecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    allow_generate_offer = fields.Boolean(
        string="Allow Generate Offer",
        help="When checked, applicants in this stage can see the 'Generate Offer' button",
        default=True
    )