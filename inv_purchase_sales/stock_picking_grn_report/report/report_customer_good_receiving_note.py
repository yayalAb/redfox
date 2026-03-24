# -*- coding: utf-8 -*-

from odoo import api, models


class ReportCustomerGoodReceivingNote(models.AbstractModel):
    # Short technical name: full name exceeds PostgreSQL 63-char identifier limit.
    _name = 'report.stock_picking_grn_report.cgrn'
    _description = 'Customer Good Receiving Note PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'data': data or {},
        }
