# -*- coding: utf-8 -*-

from odoo import api, models


class ReportDeliveryNoteAttachment(models.AbstractModel):
    _name = 'report.stock_picking_grn_report.dna'
    _description = 'Delivery Note Attachment PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)

        def invoice_ref(picking):
            if not picking.sale_id:
                return ''
            invs = picking.sale_id.invoice_ids.filtered(
                lambda m: m.state in ('posted', 'draft') and m.move_type in ('out_invoice', 'out_refund')
            )
            return ', '.join(invs.mapped('name')) if invs else ''

        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'data': data or {},
            'dna_invoice_ref': invoice_ref,
        }
