# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.misc import format_date, format_datetime


class ReportOverallCustomerDocument(models.AbstractModel):
    _name = 'report.customer_vetting.report_overall_customer_document'
    _description = 'Overall customer report PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        Report = self.env['overall.customer.report']
        docs = Report.browse(docids)
        if not docs:
            docs = Report.search([], order='partner_id, sale_order_id, id')
        docs = docs.sorted(
            key=lambda r: (
                (r.partner_id.name or '').lower(),
                r.sale_order_id.name or '',
                r.id,
            )
        )
        lines = []
        prev_partner_id = None
        for index, doc in enumerate(docs, start=1):
            doc.sequence = index
            show_ditto = bool(prev_partner_id and prev_partner_id == doc.partner_id.id)
            lines.append({
                'doc': doc,
                'show_ditto': show_ditto,
            })
            prev_partner_id = doc.partner_id.id
        order_dates = [d for d in docs.mapped('order_date') if d]
        date_from = min(order_dates) if order_dates else False
        date_to = max(order_dates) if order_dates else False
        return {
            'doc_ids': docs.ids,
            'doc_model': 'overall.customer.report',
            'docs': docs,
            'lines': lines,
            'date_from_label': format_date(self.env, date_from) if date_from else '',
            'date_to_label': format_date(self.env, date_to) if date_to else '',
            'print_date_label': format_datetime(self.env, fields.Datetime.now()),
            'company': self.env.company,
        }
