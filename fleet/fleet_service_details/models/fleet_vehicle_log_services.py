from odoo import models, fields, api


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    amount = fields.Monetary(
        string="Total Cost",
        compute='_compute_total_cost',
        store=True,
        readonly=False
    )

    service_detail_ids = fields.One2many(
        'fleet.service.detail',
        'log_id',
        string='Service Details'
    )

    @api.depends('service_detail_ids.total_cost')
    def _compute_total_cost(self):
        """Calculates and STORES the grand total cost."""
        for log in self:
            log.amount = sum(
                line.total_cost for line in log.service_detail_ids)

    @api.onchange('service_detail_ids')
    def _onchange_service_detail_ids(self):
        """
        Instantly updates the 'amount' field on the user interface when service
        lines are added, removed, or modified.
        """
        self.amount = sum(line.total_cost for line in self.service_detail_ids)
