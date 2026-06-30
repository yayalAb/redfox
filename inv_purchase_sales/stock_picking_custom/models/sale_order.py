from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    currency_id = fields.Many2one(
        readonly=False,
    )

    @api.depends('pricelist_id', 'company_id')
    def _compute_currency_id(self):
        for order in self:
            if order.pricelist_id:
                order.currency_id = (
                    order.pricelist_id.currency_id or order.company_id.currency_id
                )
            elif not order.currency_id:
                order.currency_id = order.company_id.currency_id

    proforma_checked_by_id = fields.Many2one(
        'res.users', string='Proforma Checked By', readonly=True,
    )
    fs_no = fields.Char(string='FS No')
    mrc_no = fields.Char(string='MRC No')
    payment_method = fields.Selection(
        selection=[
            ('cash', 'Cash'),
            ('credit', 'Credit'),
        ],
        string='Payment Method',
    )
    driver_name = fields.Char(string='Driver')
    driver_phone = fields.Char(string='Phone No')

    def _sync_driver_to_pickings(self):
        for order in self:
            pickings = order.picking_ids.filtered(
                lambda p: p.state not in ('done', 'cancel')
            )
            pickings.write({
                'driver_name': order.driver_name,
                'driver_phone': order.driver_phone,
            })

    def write(self, vals):
        res = super().write(vals)
        if {'driver_name', 'driver_phone'} & set(vals):
            self._sync_driver_to_pickings()
        return res

    def action_confirm(self):
        res = super().action_confirm()
        self._sync_driver_to_pickings()
        return res

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'fs_no': self.fs_no,
            'mrc_no': self.mrc_no,
            'payment_method': self.payment_method,
        })
        return invoice_vals

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
        return self.fs_no or ''

    def get_sales_attachment_mrc_no(self):
        self.ensure_one()
        return self.mrc_no or ''

    def get_sales_attachment_payment_method(self):
        self.ensure_one()
        return dict(self._fields['payment_method'].selection).get(self.payment_method, '')
