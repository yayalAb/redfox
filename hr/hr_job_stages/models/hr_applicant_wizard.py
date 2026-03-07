from odoo import models, fields, api
from odoo.fields import Command

class HrApplicantWizard(models.TransientModel):
    _name = 'hr.applicant.wizard'
    _description = 'Wizard to Change Applicant Stage'

    applicant_ids = fields.Many2many('hr.applicant', string="Applicants")
    stage_id = fields.Many2one(
        'hr.recruitment.stage',
        string='New Stage',
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_model') == 'hr.applicant' and 'applicant_ids' in fields_list:
            active_ids = self.env.context.get('active_ids', [])
            if active_ids:
                # Use Command.set to ensure proper Many2many command format
                res['applicant_ids'] = [Command.set(active_ids)]
        return res

    def action_change_stage(self):
        self.ensure_one()
        if self.applicant_ids and self.stage_id:
            self.applicant_ids.write({
                'stage_id': self.stage_id.id
            })
        return {'type': 'ir.actions.act_window_close'}