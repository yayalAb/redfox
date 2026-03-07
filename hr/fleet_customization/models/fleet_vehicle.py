from odoo import models, fields

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_rented = fields.Boolean(
        string="Is Rental", 
        help="Check this if the vehicle is rented from a third party."
    )