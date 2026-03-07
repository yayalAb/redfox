from odoo import models, fields, api

class CrmSocialMessage(models.Model):
    _name = 'crm.social.message'
    _description = 'CRM Social Message'
    _order = 'date desc'

    # REVERT: lead_id is mandatory again. Messages cannot exist without a lead.
    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')

    platform = fields.Selection([
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('email', 'Email'),
        ('other', 'Other'),
    ], required=True, string='Social Platform')

    direction = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ], required=True, default='outgoing') # Default to outgoing for manual logging

    message = fields.Text(string="Summary of Discussion", required=True)
    date = fields.Datetime(default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Logged By', default=lambda self: self.env.user)

    # Keep the "Follow Up" logic (It was part of the advanced logging, not the Inbox)
    next_action_required = fields.Boolean(string="Follow-up Required?", default=True)
    next_action_note = fields.Char(string="Next Action Plan")
    next_action_date = fields.Date(string="Follow-up Date", default=fields.Date.today)

    @api.model_create_multi
    def create(self, vals_list):
        """ 
        Automatically schedule a CRM Activity if next_action_required is checked
        """
        messages = super(CrmSocialMessage, self).create(vals_list)
        
        for msg in messages:
            if msg.next_action_required and msg.lead_id:
                msg.lead_id.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=msg.user_id.id,
                    note=f"Follow up on {msg.platform}: {msg.next_action_note or 'Check details'}",
                    date_deadline=msg.next_action_date
                )
        
        return messages