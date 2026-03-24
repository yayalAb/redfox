# -*- coding: utf-8 -*-

from odoo import api, models


class ReportGoodReceivingAttachment(models.AbstractModel):
    _name = 'report.stock_picking_grn_report.gra'
    _description = 'Good Receiving Attachment PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)

        def picking_total(picking):
            total = 0.0
            for move in picking.move_ids_without_package.filtered(lambda m: m.state != 'cancel'):
                if move.purchase_line_id:
                    qty = move.quantity or 0.0
                    total += qty * move.purchase_line_id.price_unit
            return total

        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'data': data or {},
            'gra_picking_total': picking_total,
        }
