from odoo import models, fields, api
class ResPartner(models.Model):
    _inherit = 'res.partner'

    vetting_state = fields.Selection(
        [
            ('draft', 'Not Vetted'),
            ('submitted', 'Pending Approval'),
            ('approved', 'Vetted'),
            ('rejected', 'Rejected'),
        ],
        string='Vetting Status',
        default='draft',
        required=True,
        tracking=True,  # This creates the audit trail in the chatter
        copy=False
    )

    def action_submit_for_vetting(self):
        for record in self:
            record.vetting_state = 'submitted'

    def action_approve_vetting(self):
        for record in self:
            record.vetting_state = 'approved'

    def action_reject_vetting(self):
        for record in self:
            record.vetting_state = 'rejected'

    def action_reset_to_draft(self):
        for record in self:
            record.vetting_state = 'draft'