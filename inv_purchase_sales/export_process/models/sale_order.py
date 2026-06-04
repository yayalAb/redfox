# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    export_process_id = fields.Many2one(
        'export.process',
        string='Export Process',
        copy=False,
    )
    export_process_count = fields.Integer(
        compute='_compute_export_process_count',
    )

    def _compute_export_process_count(self):
        for order in self:
            order.export_process_count = 1 if order.export_process_id else 0

    def action_view_export_process(self):
        self.ensure_one()
        if not self.export_process_id:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.process',
            'res_id': self.export_process_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
