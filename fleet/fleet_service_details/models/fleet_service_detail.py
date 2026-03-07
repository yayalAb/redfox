from odoo import models, fields, api


class FleetServiceDetail(models.Model):
    _name = 'fleet.service.detail'
    _description = 'Fleet Service Detail Lines'

    log_id = fields.Many2one(
        'fleet.vehicle.log.services',
        string='Service Log',
        required=True,
        ondelete='cascade'
    )

    currency_id = fields.Many2one(
        related='log_id.currency_id',
        string='Currency'
    )

    name = fields.Char(
        string='Sub-Service Type',
        required=True
    )

    product_uom_qty = fields.Float(
        string='Quantity',
        required=True,
        default=1.0
    )

    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measurement',
        required=True
    )

    cost_per_unit = fields.Monetary(
        string='Cost per Unit',
        required=True
    )

    total_cost = fields.Monetary(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True
    )

    @api.depends('product_uom_qty', 'cost_per_unit')
    def _compute_total_cost(self):
        """Calculates the total cost for this specific line."""
        for line in self:
            line.total_cost = line.product_uom_qty * line.cost_per_unit
