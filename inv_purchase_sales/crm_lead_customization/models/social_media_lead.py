from odoo import models, fields, api
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    social_platform = fields.Selection([
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('other', 'Other'),
    ], string='Social Platform', tracking=True)

    # Renamed for clarity, but you can keep 'social_account' if you prefer
    social_account = fields.Char(
        string='Account/Number', 
        help="Phone number for WA (e.g. 251911...), Username for Telegram",
        tracking=True
    )

    social_profile_url = fields.Char(string='Full Profile URL', tracking=True)

    # --- RELATIONS ---
    social_message_ids = fields.One2many(
        'crm.social.message', 'lead_id', string="Social Messages" )

    social_message_count = fields.Integer(
        string="Message Count",
        compute='_compute_social_message_count'
    )

    @api.depends('social_message_ids')
    def _compute_social_message_count(self):
        for lead in self:
            lead.social_message_count = len(lead.social_message_ids)

    # --- CLICK-TO-CHAT LOGIC ---
    def action_open_social_chat(self):
        """ Opens the social media link in a new tab """
        self.ensure_one()
        url = self._get_social_url()
        if not url:
            raise UserError("Please select a Platform and enter an Account/Number to start a chat.")
        
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def _get_social_url(self):
        """ Helper to construct URLs based on platform """
        if not self.social_platform or not self.social_account:
            return self.social_profile_url or False
            
        account = self.social_account.strip()
        
        if self.social_platform == 'whatsapp':
            # Remove + signs or spaces for WA URL
            clean_number = ''.join(filter(str.isdigit, account))
            return f"https://wa.me/{clean_number}"
        elif self.social_platform == 'telegram':
            return f"https://t.me/{account.replace('@', '')}"
        elif self.social_platform == 'facebook':
            return f"https://m.me/{account}"
        elif self.social_platform == 'instagram':
            return f"https://instagram.com/{account.replace('@', '')}"
        elif self.social_platform == 'linkedin':
             # LinkedIn usually requires full URL, but we try search if just name
            return f"https://www.linkedin.com/search/results/all/?keywords={account}"
        
        return self.social_profile_url

    # --- LOG INTERACTION LOGIC ---
    def action_log_social_interaction(self):
        """ Opens a pop-up to create a new social message """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Log Social Interaction',
            'res_model': 'crm.social.message',
            'view_mode': 'form',
            'target': 'new', # Opens as a modal popup
            'context': {
                'default_lead_id': self.id,
                'default_platform': self.social_platform,
                'default_user_id': self.env.user.id,
            }
        }