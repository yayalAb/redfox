from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    period_type = fields.Selection([
        ('quarter', 'Quarter'),
        ('half', 'Semi-Annual'),
        ('year', 'Annual'),
    ], string="Appraisal Period Type",
       default='quarter',
       config_parameter='hr_appraisal.period_type')
