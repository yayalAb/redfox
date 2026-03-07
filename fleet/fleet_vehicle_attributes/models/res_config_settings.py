from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    initial_fuel_deposit = fields.Float(
        string='Initial Fuel Deposit',
        config_parameter='fleet.initial_fuel_deposit',
        help="The initial fuel deposit amount for vehicles."
    )

    used_fuel_deposit = fields.Float(
        string='Used Fuel Deposit',
        config_parameter='fleet.used_fuel_deposit',
        help="Used fuel deposit amount for vehicles."
    )