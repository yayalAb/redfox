import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class CrmFacebookPost(models.Model):
    _name = 'crm.facebook.post'
    _description = 'Facebook Incoming Post'
    _order = 'post_time desc'
    _rec_name = 'author_name'

    # --- RAW FACEBOOK DATA ---
    social_id = fields.Char(string="Facebook Post ID", readonly=True, copy=False)
    author_name = fields.Char(string="Author", required=True)
    message = fields.Text(string="Post Content")
    post_time = fields.Datetime(string="Posted Time")
    permalink_url = fields.Char(string="Facebook Link")
    
    # --- PROCESSING STATUS ---
    state = fields.Selection([
        ('new', 'New'),
        ('converted', 'Converted to Lead'),
        ('ignored', 'Ignored')
    ], string="Status", default='new', readonly=True)

    # Link to CRM (Optional, filled after conversion)
    created_lead_id = fields.Many2one('crm.lead', string="Created Lead", readonly=True)

    # --- 1. FETCH LOGIC (API) ---
    @api.model
    def fetch_facebook_feed(self):
        """ Fetch data from Facebook and store in THIS model only """
        config = self.env['ir.config_parameter'].sudo()
        page_token = config.get_param('facebook.page.token')
        page_id = config.get_param('facebook.page.id')

        if not page_token or not page_id:
            _logger.warning("Facebook Credentials missing.")
            return

        url = f"https://graph.facebook.com/v24.0/{page_id}/feed"
        params = {
            'access_token': page_token,
            'fields': 'id,message,created_time,from,permalink_url',
            'limit': 15
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if 'data' in data:
                for post in data['data']:
                    fb_id = post.get('id')
                    
                    # Prevent Duplicates
                    if self.search_count([('social_id', '=', fb_id)]):
                        continue

                    # Create Record in the NEW table
                    self.create({
                        'social_id': fb_id,
                        'author_name': post.get('from', {}).get('name', 'Anonymous'),
                        'message': post.get('message', '[Media/Photo Post]'),
                        'post_time': fields.Datetime.now(), # Simplified
                        'permalink_url': post.get('permalink_url'),
                        'state': 'new'
                    })
        except Exception as e:
            _logger.error(f"FB Fetch Error: {str(e)}")

    # --- 2. CONVERT TO LEAD LOGIC ---
    def action_create_lead(self):
        self.ensure_one()
        if self.created_lead_id:
            return

        # Create the CRM Lead
        lead = self.env['crm.lead'].create({
            'name': f"FB Inquiry: {self.author_name}",
            'contact_name': self.author_name,
            'social_platform': 'facebook', # Uses your Phase 1 field
            'social_profile_url': self.permalink_url, # Uses your Phase 1 field
            'description': f"Imported from Facebook.\n\nMessage:\n{self.message}",
            'user_id': self.env.user.id,
        })

        # Update this record
        self.write({
            'state': 'converted',
            'created_lead_id': lead.id
        })

        # Open the new Lead
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'res_id': lead.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_ignore(self):
        self.write({'state': 'ignored'})
    
    # ... inside class CrmFacebookPost ...

    def action_debug_connection(self):
        """ 
        Debug method to show Raw Facebook Data in a popup 
        """
        # 1. Get Credentials
        config = self.env['ir.config_parameter'].sudo()
        page_token = config.get_param('facebook.page.token')
        page_id = config.get_param('facebook.page.id')

        if not page_token or not page_id:
            raise UserError(f"Missing Credentials!\nID: {page_id}\nToken: {page_token}")

        # 2. Call API Manually
        url = f"https://graph.facebook.com/v24.0/{page_id}/feed"
        params = {
            'access_token': page_token,
            'fields': 'id,message,created_time,from', # Simple fields
            'limit': 5
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            # 3. FORCE A POPUP WITH THE RESULT
            raise UserError(f"Page ID: {page_id}\nHTTP Code: {response.status_code}\n\nRAW DATA:\n{response.text}")
        except Exception as e:
            raise UserError(f"Connection Failed: {str(e)}")