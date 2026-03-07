# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ServiceRequest(models.Model):
    _inherit = 'service.request'

    agreement_id = fields.Many2one(
        'sale.agreement',
        string='Contract Agreement',
        copy=False,
        index=True,
        readonly=True
    )

    def action_create_client_maintenance(self):
        self.ensure_one()

        context = {
            'default_agreement_id': self.agreement_id.id,
            'default_product_id': self.product_id.id,
            'default_product_qty': self.quantity,
            'default_production_type': 'maintenance',
            'default_service_request': self.id,
            'default_origin': self.name
        }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Service Maintenance',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'target': 'current',
            'context': context,
        }
    
    def action_open_client_maintenance(self):
        self.ensure_one()

        return {
            'name': 'Client Maintenance',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mrp.production',
            'domain': [('service_request', '=', self.id)],
            'context': {
                'default_service_request': self.id,
            }
        }

