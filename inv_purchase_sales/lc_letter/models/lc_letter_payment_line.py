# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command
from odoo.exceptions import AccessError, UserError
from odoo.tools.translate import _
from odoo.tools.image import image_data_uri


class LcLetterPaymentLine(models.Model):
    _name = 'lc.letter.payment.line'
    _description = 'LC Letter Payment Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    lc_letter_id = fields.Many2one(
        'lc.letter',
        string='LC Number',
        required=True,
        ondelete='cascade',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('authorized', 'Authorized'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    submitted_by = fields.Many2one(
        'res.users', string='Submitted by', readonly=True, tracking=True)
    verified_by = fields.Many2one(
        'res.users', string='Verified by', readonly=True, tracking=True)
    authorized_by = fields.Many2one(
        'res.users', string='Authorized by', readonly=True, tracking=True)
    approved_by = fields.Many2one(
        'res.users', string='Approved by', readonly=True, tracking=True)

    def action_submit(self):
        self.check_access_rights('write')
        if not self.env.user.has_group('lc_letter.group_lc_payment_submit'):
            raise AccessError(
                _('You do not have permission to submit payment lines.'))
        self.write({'state': 'submitted', 'submitted_by': self.env.user.id})

    def action_verify(self):
        self.check_access_rights('write')
        if not self.env.user.has_group('lc_letter.group_lc_payment_verify'):
            raise AccessError(
                _('You do not have permission to verify payment lines.'))
        self.write({'state': 'verified', 'verified_by': self.env.user.id})

    def action_authorize(self):
        self.check_access_rights('write')
        if not self.env.user.has_group('lc_letter.group_lc_payment_authorize'):
            raise AccessError(
                _('You do not have permission to authorize payment lines.'))
        self.write({'state': 'authorized', 'authorized_by': self.env.user.id})

    def action_approve(self):
        self.check_access_rights('write')
        self.write({'state': 'approved', 'approved_by': self.env.user.id})
        if not self.env.user.has_group('lc_letter.group_lc_payment_approve'):
            raise AccessError(
                _('You do not have permission to approve payment lines.'))
        for line in self:
            line._action_approve_single()

    def _action_approve_single(self):
        """Create vendor bill, attach payment request PDF to payment line and bill."""
        self.ensure_one()
        if self.vendor_bill_id:
            return  # Already has bill (e.g. reset and re-approve)
        # 1. Create vendor bill
        product = self.product_id
        if not product:
            raise UserError(_('Product is required on the payment line.'))
        if product.type != 'service':
            product = self.env['product.product'].search(
                [('type', '=', 'service')], limit=1
            )
            if not product:
                raise UserError(_(
                    'No service product found. Please use a service product on '
                    'the payment line or create one.'
                ))
        company = self.lc_letter_id.company_id or self.env.company
        journal = self.env['account.journal'].search(
            [('company_id', '=', company.id), ('type', '=', 'purchase')],
            limit=1
        )
        if not journal:
            raise UserError(
                _('No purchase journal found for company %s.', company.name))
        bill_vals = {
            'move_type': 'in_invoice',
            'journal_id': journal.id,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'invoice_origin': _('LC Payment Request %s') % self.doc_no,
            'ref': self.doc_no,
            'invoice_line_ids': [
                Command.create({
                    'product_id': product.id,
                    'quantity': 1,
                    'price_unit': self.amount,
                    'name': product.display_name,
                    'is_landed_costs_line': True,
                }),
            ],
        }
        bill = self.env['account.move'].with_company(company).create(bill_vals)
        self.vendor_bill_id = bill

        # 2. Generate Payment Request PDF and attach to payment line
        report = self.env.ref('lc_letter.action_report_payment_request')
        pdf_content, _dummy = self.env['ir.actions.report'].with_context(
            lang=self.env.user.lang
        )._render_qweb_pdf(report, self.ids)
        pdf_name = _('Payment_Request_%s') % (self.doc_no or 'report')
        att_vals = {
            'name': f'{pdf_name}.pdf',
            'type': 'binary',
            'raw': pdf_content,
            'res_model': self._name,
            'res_id': self.id,
        }
        payment_att = self.env['ir.attachment'].create(att_vals)
        self.attachment_ids = [(4, payment_att.id)]

        # 3. Attach the same PDF to the bill chatter
        bill_att_vals = {
            'name': att_vals['name'],
            'type': 'binary',
            'raw': pdf_content,
            'res_model': bill._name,
            'res_id': bill.id,
        }
        bill_att = self.env['ir.attachment'].create(bill_att_vals)
        bill.message_post(
            body=_('Payment Request form attached from LC payment approval.'),
            attachment_ids=[bill_att.id],
        )

    def action_reject(self):
        self.check_access_rights('write')
        if not self.env.user.has_group('lc_letter.group_lc_payment_reject'):
            raise AccessError(
                _('You do not have permission to reject payment lines.'))
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.check_access_rights('write')
        if not self.env.user.has_group('lc_letter.group_lc_payment_cancel'):
            raise AccessError(
                _('You do not have permission to cancel payment lines.'))
        self.write({'state': 'cancelled'})

    @api.depends('lc_letter_id')
    def _compute_purchase_order_count(self):
        for line in self:
            if line.lc_letter_id:
                line.purchase_order_count = self.env['purchase.order'].search_count([
                    ('lc_letter_id', '=', line.lc_letter_id.id),
                ])
            else:
                line.purchase_order_count = 0

    def action_view_purchase_orders(self):
        self.ensure_one()
        if not self.lc_letter_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('lc_letter_id', '=', self.lc_letter_id.id)],
            'context': {'default_lc_letter_id': self.lc_letter_id.id},
        }

    def action_open_vendor_bill(self):
        self.ensure_one()
        if not self.vendor_bill_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.vendor_bill_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_reset_draft(self):
        self.check_access_rights('write')
        if not self.env.user.has_group('lc_letter.group_lc_payment_reset_draft'):
            raise AccessError(
                _('You do not have permission to reset payment lines to draft.'))
        self.write({
            'state': 'draft',
            'submitted_by': False,
            'verified_by': False,
            'authorized_by': False,
            'approved_by': False,
            'vendor_bill_id': False,
        })
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lc_letter_payment_line_ir_attachment_rel',
        'payment_line_id',
        'attachment_id',
        string='Attachments',
    )
    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        related='lc_letter_id.currency_id',
        store=True,
    )
    note = fields.Html(string='Note')

    order_no = fields.Char(
        string='Order No',
        copy=False,
        default='/',
        help='Sequential order number for payment request',
    )
    declaration_no = fields.Char(string='Declaration No')
    payment_type = fields.Selection([
        ('cpo', 'CPO'),
        ('transfer', 'Transfer'),
        ('cheque', 'Cheque'),
    ], string='Payment Type')
    account_number = fields.Char(string='Account Number')
    account_type = fields.Selection([
        ('direct', 'Direct'),
        ('deposit', 'Deposit'),
    ], string='Account Type')
    doc_no = fields.Char(
        string='Doc No',
        copy=False,
        default='/',
        help='Payment Request document number',
    )

    vendor_bill_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        copy=False,
        readonly=True,
        help='Vendor bill created on approval',
    )
    purchase_order_count = fields.Integer(
        string='Purchase Order Count',
        compute='_compute_purchase_order_count',
    )

    amount_in_words = fields.Char(
        string='Amount in Words',
        compute='_compute_amount_in_words',
    )

    @api.depends('amount', 'currency_id')
    def _compute_amount_in_words(self):
        for line in self:
            if line.currency_id and line.amount:
                line.amount_in_words = line.currency_id.amount_to_text(
                    line.amount)
            else:
                line.amount_in_words = ''

    def _get_user_signature_data_uri(self, user):
        """Return data URI for user's sign_signature, or empty string if not available."""
        if not user:
            return ''
        sig = getattr(user, 'sign_signature', None)
        if not sig:
            return ''
        try:
            if isinstance(sig, str):
                sig = sig.encode('ascii')
            elif not isinstance(sig, bytes):
                sig = bytes(sig)
            return image_data_uri(sig)
        except Exception:
            return ''

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('doc_no', '/') == '/':
                vals['doc_no'] = self.env['ir.sequence'].next_by_code(
                    'lc.payment.request.doc') or '/'
            if vals.get('order_no', '/') == '/':
                vals['order_no'] = self.env['ir.sequence'].next_by_code(
                    'lc.payment.request.order') or '/'
        return super().create(vals_list)
