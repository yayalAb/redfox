from odoo import models, fields, api

class BlacklistWizard(models.TransientModel):
    _name = 'supplies.blacklist.wizard'
    _description = 'Blacklist Wizard'

    email = fields.Char(string='Email', required=True)
    reason = fields.Text(string='Reason')
    registration_id = fields.Many2one('supplies.registration', string='Registration')

    def action_blacklist(self):
        self.ensure_one()
        existing_blacklist = self.env['mail.blacklist'].search([('email', '=', self.email)])
        if existing_blacklist:
            existing_blacklist.write({'reason': self.reason})
        else:
            self.env['mail.blacklist'].create({'email': self.email, 'reason': self.reason})
        self.registration_id.write({'state': 'blacklisted'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'supplies.registration',
            'view_mode': 'form',
            'res_id': self.registration_id.id,
        }