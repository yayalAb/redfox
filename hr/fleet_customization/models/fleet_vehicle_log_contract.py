from odoo import models, fields, api

class FleetVehicleLogContract(models.Model):
    _inherit = "fleet.vehicle.log.contract"
    
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=False)