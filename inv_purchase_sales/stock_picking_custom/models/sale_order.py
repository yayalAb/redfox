from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    proforma_checked_by_id = fields.Many2one(
        'res.users', string='Proforma Checked By', readonly=True,
    )

    def get_proforma_amount_in_words(self):
        self.ensure_one()
        total = self.amount_total
        currency = self.currency_id or self.company_id.currency_id
        if not currency or not total:
            return ''
        return currency.amount_to_text(total)

    def get_proforma_prepared_by(self):
        self.ensure_one()
        return getattr(self, 'prepared_by_id', False) or self.create_uid

    def get_proforma_approved_by(self):
        self.ensure_one()
        return getattr(self, 'approved_by_id', False) or False

    def get_proforma_prepared_date(self):
        self.ensure_one()
        if getattr(self, 'prepared_date', False):
            return self.prepared_date
        return self.date_order.date() if self.date_order else False

    def get_proforma_approved_date(self):
        self.ensure_one()
        if getattr(self, 'approved_date', False):
            return self.approved_date
        if self.state == 'sale' and self.write_date:
            return self.write_date.date()
        return False

    def get_proforma_line_remark(self, line):
        return getattr(line, 'report_remark', False) or ''

    def get_proforma_tin(self):
        self.ensure_one()
        if getattr(self, 'partner_tin', False):
            return self.partner_tin
        return self.partner_id.vat or ''

    def get_proforma_term_condition(self):
        self.ensure_one()
        if getattr(self, 'report_remark', False):
            return self.report_remark
        return self.note or ''

    def get_proforma_order_lines(self):
        self.ensure_one()
        return self.order_line.filtered(lambda line: not line.display_type)

    def get_sales_attachment_fs_no(self):
        self.ensure_one()
        invoices = self.invoice_ids.filtered(
            lambda move: move.move_type == 'out_invoice' and move.state == 'posted'
        )
        return invoices[0].name if invoices else ''

    def get_sales_attachment_mrc_no(self):
        self.ensure_one()
        return self.client_order_ref or ''

    def get_sales_attachment_payment_method(self):
        self.ensure_one()
        if not self.payment_term_id:
            return ''
        term = self.payment_term_id
        name = (term.name or '').lower()
        if 'cash' in name or 'immediate' in name:
            return 'Cash'
        if 'credit' in name:
            return 'Credit'
        if term.line_ids and all(line.nb_days == 0 for line in term.line_ids):
            return 'Cash'
        return 'Credit'
