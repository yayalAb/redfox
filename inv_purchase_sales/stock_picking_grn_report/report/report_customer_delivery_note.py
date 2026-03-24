# -*- coding: utf-8 -*-
from odoo import api, models


class ReportCustomerDeliveryNote(models.AbstractModel):
    _name = 'report.stock_picking_grn_report.report_customer_delivery_note'
    _description = 'Customer Delivery Note PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
        }
