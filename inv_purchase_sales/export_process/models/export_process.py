# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ExportProcess(models.Model):
    _name = 'export.process'
    _description = 'Export Process'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Quotation / Sales Order',
        copy=False,
        tracking=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
        tracking=True,
    )
    line_ids = fields.One2many(
        'export.process.line',
        'export_id',
        string='Products',
        copy=True,
    )
    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_amount_total',
        store=True,
        currency_field='currency_id',
    )

    # --- Quotation & contract ---
    customer_response = fields.Selection([
        ('pending', 'Pending'),
        ('yes', 'Approved'),
        ('no', 'Rejected'),
    ], string='Customer Response', default='pending', tracking=True)
    contract_notes = fields.Html(string='Contract Agreement')
    bag_mark_sent = fields.Boolean(string='Bag Mark Sent to Customer', tracking=True)
    sample_approval_sent = fields.Boolean(string='Sample Approval Sent', tracking=True)

    payment_method = fields.Selection([
        ('cad', 'Cash Against Documents (CAD)'),
        ('lc', 'Letter of Credit (LC)'),
        ('tt', 'Telegraphic Transfer (T/T)'),
    ], string='Payment Method', tracking=True)
    lc_opened = fields.Boolean(string='LC Opened', tracking=True)
    tt_before_shipment_paid = fields.Boolean(
        string='Before-Shipment Payment (T/T)',
        tracking=True,
    )
    after_shipment_paid = fields.Boolean(string='After-Shipment Payment', tracking=True)
    final_payment_collected = fields.Boolean(string='Final Payment Collected', tracking=True)
    nbe_settlement_done = fields.Boolean(string='NBE Settlement Done', tracking=True)

    # --- Parallel tracks ---
    doc_track_state = fields.Selection([
        ('not_started', 'Not Started'),
        ('prepare', 'Prepare Shipment Document'),
        ('draft_review', 'Review Draft Document'),
        ('sent_transporter', 'Sent to Transporter'),
        ('approved', 'Final Document Approved'),
    ], string='Documentation Track', default='not_started', tracking=True)
    logistics_track_state = fields.Selection([
        ('not_started', 'Not Started'),
        ('booking', 'Booking Requested'),
        ('inspection', 'Product Inspection'),
        ('shipment', 'Processed to Shipment'),
        ('status_sent', 'Status Sent to Customer'),
    ], string='Logistics Track', default='not_started', tracking=True)

    shipping_line_id = fields.Many2one(
        'res.partner',
        string='Shipping Line',
        domain=[('is_company', '=', True)],
    )
    transporter_id = fields.Many2one(
        'res.partner',
        string='Transporter',
        domain=[('is_company', '=', True)],
    )
    shipping_instruction_date = fields.Date(string='Shipping Instruction Date')
    shipment_date = fields.Date(string='Shipment Date')
    notes = fields.Html(string='Internal Notes')

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('cancelled', 'Quotation Cancelled'),
        ('quotation_confirmed', 'Quotation Confirmed'),
        ('contract', 'Contract'),
        ('payment_setup', 'Payment Setup'),
        ('shipping_instruction', 'Shipping Instruction'),
        ('processing', 'In Progress'),
        ('shipped', 'Shipped'),
        ('final_payment', 'Final Payment'),
        ('nbe_settlement', 'NBE Settlement'),
        ('done', 'Done'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    payment_count = fields.Integer(compute='_compute_payment_count')

    @api.depends('partner_id')
    def _compute_payment_count(self):
        Payment = self.env['account.payment']
        for rec in self:
            rec.payment_count = Payment.search_count([
                ('partner_id', '=', rec.partner_id.id),
                ('payment_type', '=', 'inbound'),
            ]) if rec.partner_id else 0

    @api.depends('line_ids.subtotal')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('subtotal'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.process') or _('New')
        return super().create(vals_list)

    # --- Quotation phase ---
    def action_create_quotation(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Add at least one product line before creating a quotation.'))
        if self.sale_order_id:
            raise UserError(_('A quotation is already linked to this export process.'))

        order_lines = []
        for line in self.line_ids:
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name or line.product_id.display_name,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'price_unit': line.price_unit,
            }))

        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'order_line': order_lines,
            'origin': self.name,
            'export_process_id': self.id,
        })
        self.sale_order_id = sale_order.id
        self.message_post(body=_('Quotation %s created.') % sale_order.name)
        return self.action_view_sale_order()

    def action_confirm_quotation(self):
        for rec in self:
            if rec.customer_response != 'yes':
                raise UserError(_('Set customer response to Approved before confirming.'))
            rec.state = 'quotation_confirmed'

    def action_cancel_quotation(self):
        for rec in self:
            rec.customer_response = 'no'
            rec.state = 'cancelled'
            if rec.sale_order_id and rec.sale_order_id.state in ('draft', 'sent'):
                rec.sale_order_id.action_cancel()

    # --- Contract phase ---
    def action_prepare_contract(self):
        for rec in self:
            if rec.state not in ('quotation_confirmed', 'contract'):
                raise UserError(_('Confirm the quotation first.'))
            rec.state = 'contract'

    def action_send_bag_mark(self):
        for rec in self:
            rec.bag_mark_sent = True
            rec.message_post(body=_('Bag mark approval sent to customer.'))

    def action_send_sample_approval(self):
        for rec in self:
            rec.sample_approval_sent = True
            rec.message_post(body=_('Sample approval sent to customer.'))

    def action_contract_complete(self):
        for rec in self:
            if not rec.bag_mark_sent or not rec.sample_approval_sent:
                raise UserError(
                    _('Send bag mark approval and sample approval to the customer first.')
                )
            rec.state = 'payment_setup'

    # --- Payment method branch ---
    def action_confirm_payment_method(self):
        for rec in self:
            if not rec.payment_method:
                raise UserError(_('Select a payment method (CAD, LC, or T/T).'))
            if rec.payment_method == 'lc' and not rec.lc_opened:
                raise UserError(_('Open the Letter of Credit before continuing.'))
            if rec.payment_method == 'tt' and not rec.tt_before_shipment_paid:
                raise UserError(
                    _('Collect before-shipment payment (T/T) via Accounting first.')
                )
            rec.state = 'shipping_instruction'

    def action_mark_lc_opened(self):
        for rec in self:
            if rec.payment_method != 'lc':
                raise UserError(_('Payment method must be Letter of Credit.'))
            rec.lc_opened = True
            rec.message_post(body=_('Letter of Credit opened.'))

    def action_mark_tt_before_paid(self):
        for rec in self:
            if rec.payment_method != 'tt':
                raise UserError(_('Payment method must be Telegraphic Transfer.'))
            rec.tt_before_shipment_paid = True
            rec.message_post(body=_('Before-shipment payment recorded.'))

    # --- Shipping instruction & parallel tracks ---
    def action_request_shipping_instruction(self):
        for rec in self:
            rec.shipping_instruction_date = fields.Date.today()
            rec.state = 'processing'
            rec.message_post(body=_('Shipping instruction requested from customer.'))

    def _advance_doc_track(self, expected, new_state, label):
        for rec in self:
            if rec.doc_track_state != expected:
                raise UserError(_('Complete the previous documentation step first.'))
            rec.doc_track_state = new_state
            rec.message_post(body=label)

    def action_doc_prepare(self):
        self._advance_doc_track(
            'not_started', 'prepare', _('Shipment document preparation started.'))

    def action_doc_review_draft(self):
        self._advance_doc_track(
            'prepare', 'draft_review', _('Draft document under review.'))

    def action_doc_send_transporter(self):
        for rec in self:
            if rec.doc_track_state != 'draft_review':
                raise UserError(_('Complete draft review before sending to transporter.'))
            if not rec.transporter_id:
                raise UserError(_('Select a transporter.'))
            rec.doc_track_state = 'sent_transporter'
            rec.message_post(body=_('Documents sent to transporter %s.') % rec.transporter_id.name)

    def action_doc_approve_final(self):
        self._advance_doc_track(
            'sent_transporter', 'approved', _('Final shipment documents approved.'))

    def _advance_logistics_track(self, expected, new_state, label):
        for rec in self:
            if rec.logistics_track_state != expected:
                raise UserError(_('Complete the previous logistics step first.'))
            rec.logistics_track_state = new_state
            rec.message_post(body=label)

    def action_logistics_booking(self):
        for rec in self:
            if not rec.shipping_line_id:
                raise UserError(_('Select a shipping line.'))
            rec.logistics_track_state = 'booking'
            rec.message_post(body=_('Booking requested with %s.') % rec.shipping_line_id.name)

    def action_logistics_inspection(self):
        self._advance_logistics_track(
            'booking', 'inspection', _('Product inspection completed.'))

    def action_logistics_shipment(self):
        self._advance_logistics_track(
            'inspection', 'shipment', _('Product processed to shipment.'))
        for rec in self:
            rec.shipment_date = fields.Date.today()

    def action_logistics_status_to_customer(self):
        self._advance_logistics_track(
            'shipment', 'status_sent', _('Shipment status sent to customer.'))

    def action_mark_after_shipment_paid(self):
        for rec in self:
            rec.after_shipment_paid = True
            rec.message_post(body=_('After-shipment payment collected.'))

    def _check_tracks_ready_to_ship(self):
        self.ensure_one()
        if self.doc_track_state != 'approved':
            raise UserError(_('Approve final shipment documents first.'))
        if self.logistics_track_state != 'status_sent':
            raise UserError(_('Complete logistics and send shipment status to customer.'))

    def action_confirm_shipped(self):
        for rec in self:
            rec._check_tracks_ready_to_ship()
            if rec.payment_method == 'tt' and not rec.after_shipment_paid:
                raise UserError(_('Collect after-shipment payment before confirming shipment.'))
            rec.state = 'shipped'

    def action_collect_final_payment(self):
        for rec in self:
            if rec.state != 'shipped':
                raise UserError(_('Confirm shipment before collecting final payment.'))
            rec.final_payment_collected = True
            rec.state = 'final_payment'
            rec.message_post(body=_('Final payment collected.'))

    def action_nbe_settlement(self):
        for rec in self:
            if not rec.final_payment_collected:
                raise UserError(_('Collect final payment before NBE settlement.'))
            rec.nbe_settlement_done = True
            rec.state = 'nbe_settlement'
            rec.message_post(body=_('Settlement payment provided to NBE.'))

    def action_done(self):
        for rec in self:
            if not rec.nbe_settlement_done:
                raise UserError(_('Complete NBE settlement first.'))
            rec.state = 'done'

    def action_reset_to_draft(self):
        for rec in self.filtered(lambda r: r.state in ('cancelled',)):
            rec.write({
                'state': 'draft',
                'customer_response': 'pending',
            })

    # --- Navigation ---
    def action_view_sale_order(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_('No quotation linked yet. Create a quotation first.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quotation'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_customer_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Payments'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.partner_id.id), ('payment_type', '=', 'inbound')],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
            },
        }


class ExportProcessLine(models.Model):
    _name = 'export.process.line'
    _description = 'Export Process Line'

    export_id = fields.Many2one(
        'export.process',
        string='Export Process',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    name = fields.Char(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='UoM',
        related='product_id.uom_id',
        store=True,
        readonly=False,
    )
    price_unit = fields.Monetary(string='Unit Price', currency_field='currency_id')
    currency_id = fields.Many2one(related='export_id.currency_id')
    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
        currency_field='currency_id',
    )

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.price_unit = self.product_id.lst_price
