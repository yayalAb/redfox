# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    service_request_id = fields.Many2one(
        'service.request',
        string='Service request',
        ondelete='set null',
        copy=False,
        index=True,
    )

    _sql_constraints = [
        (
            'customer_vetting_service_request_unique',
            'unique(service_request_id)',
            'Each service request can only be linked to one sales order.',
        ),
    ]
