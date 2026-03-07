from odoo import models, fields

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    quantity = fields.Integer(string='Quantity', default=1)