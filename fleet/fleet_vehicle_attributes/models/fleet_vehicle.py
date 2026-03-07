from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    motor_number = fields.Char(string='Motor Number')
    cc = fields.Integer(string='CC')
    is_rented = fields.Boolean(string='Is Rented', default=False)


    @api.constrains('license_plate')
    def _check_license_plate_unique(self):
        for record in self:
            if record.license_plate:
                existing = self.search_count([
                    ('license_plate', '=', record.license_plate),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError("License Plate must be unique.")
