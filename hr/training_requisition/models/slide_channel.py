from odoo import models, fields, api

class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    resource_line_ids = fields.One2many(
        'resource.lines', 'channel_id', string='Resource Lines')
    
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date') 
    training_requisition_id = fields.Many2one('training.requisition', string='Origin Requisition')
        