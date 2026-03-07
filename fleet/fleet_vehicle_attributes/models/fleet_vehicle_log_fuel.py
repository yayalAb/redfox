from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FleetVehicleLogFuel(models.Model):
    _inherit = "fleet.vehicle.log.fuel"

    fuel_deposit_id = fields.Many2one(
        'fuel.deposit',
        string="Fuel Deposit",
        default=lambda self: self.env['fuel.deposit'].search([('is_active', '=', True)], limit=1)
    )
    remaining_deposit_amount = fields.Monetary(string="Remaining Deposit Amount", related='fuel_deposit_id.remaining_amount')
    last_recorded_odometer = fields.Float(
        string="Last Recorded Odometer",
        compute="_compute_last_recorded_odometer",
        store=True
    )
    used_miles = fields.Float(
        string="Used Miles",
        compute="_compute_used_miles",
        store=True
    )

    used_miles_per_liter = fields.Float(string='Used Miles (per Liter)', compute='_compute_used_miles_per_liter', store=True)

    @api.depends('vehicle_id', 'date', 'odometer')
    def _compute_last_recorded_odometer(self):
        for record in self:
            record.last_recorded_odometer = 0.0

            if not record.vehicle_id or not record.date:
                continue

            last_log = self.env['fleet.vehicle.log.fuel'].search(
                [
                    ('vehicle_id', '=', record.vehicle_id.id),
                    ('date', '<=', record.date),
                ],
                order="date desc, id desc",
                limit=2
            )

            # Always defined now
            last_log = last_log - record
            if last_log:
                record.last_recorded_odometer = last_log[0].odometer



    @api.depends('odometer', 'last_recorded_odometer')
    def _compute_used_miles(self):
        """
        Difference between current odometer and last recorded odometer.
        """
        for record in self:
            record.used_miles = (
                record.odometer - record.last_recorded_odometer
                if record.odometer and record.last_recorded_odometer
                else 0.0
            )
    
    @api.depends('used_miles', 'liter')
    def _compute_used_miles_per_liter(self):
        for record in self:
            if record.used_miles and record.liter:
                record.used_miles_per_liter = record.used_miles / record.liter

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('fuel_deposit_id'):
                active_deposit = self.env['fuel.deposit'].search([('is_active', '=', True)], limit=1)
                if not active_deposit:
                    raise ValidationError("No active fuel deposit available. Please create one before logging fuel.")
                vals['fuel_deposit_id'] = active_deposit.id
        return super().create(vals_list)

    @api.constrains('remaining_deposit_amount', 'cost')
    def _check_fuel_deposit(self):
        for record in self:
            if record.cost > record.remaining_deposit_amount:
                raise ValidationError("Insufficient fuel deposit.")
