from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    meal_price = fields.Float(
        string='Meal Price',
        config_parameter='lunch_management.meal_price',
        help="The standard price of a company-provided meal."
    )