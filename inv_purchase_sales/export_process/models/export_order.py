# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

EXPORT_STAGES = [
    ('quotation', 'Quotation'),
    ('contract', 'Contract'),
    ('sample_approval', 'Sample Approval'),
    ('bag_mark', 'Bag Mark Approval'),
    ('payment_setup', 'Payment Setup'),
    ('payment_process', 'LC / CAD / TT'),
    ('shipping_instruction', 'Shipping Instruction'),
    ('booking', 'Booking'),
    ('inspection', 'Inspection'),
    ('shipment', 'Shipment'),
    ('documentation', 'Documentation'),
    ('payment_collection', 'Payment Collection'),
    ('nbe_settlement', 'NBE Settlement'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


class ExportOrder(models.Model):
    _name = 'export.export.order'
    _description = 'Export Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Quotation',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    partner_id = fields.Many2one(
        related='sale_order_id.partner_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related='sale_order_id.company_id',
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        related='sale_order_id.currency_id',
        store=True,
        readonly=True,
    )
    user_id = fields.Many2one(
        related='sale_order_id.user_id',
        store=True,
        readonly=True,
    )
    destination_country_id = fields.Many2one(
        related='sale_order_id.destination_country_id',
        store=True,
    )
    incoterm_id = fields.Many2one(
        related='sale_order_id.incoterm_id',
        store=True,
    )
    export_payment_method = fields.Selection(
        [
            ('lc', 'Letter of Credit'),
            ('cad', 'Cash Against Document'),
            ('tt', 'Telegraphic Transfer'),
        ],
        string='Export Payment Method',
        related='sale_order_id.export_payment_method',
        store=True,
        readonly=False,
    )
    amount_total = fields.Monetary(
        related='sale_order_id.amount_total',
        store=True,
    )

    quotation_state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], string='Quotation Status', default='draft', tracking=True)

    state = fields.Selection(
        EXPORT_STAGES,
        string='Stage',
        default='quotation',
        required=True,
        tracking=True,
        copy=False,
        group_expand='_read_group_stage_ids',
    )
    color = fields.Integer(compute='_compute_color')

    contract_id = fields.Many2one('export.contract', string='Contract', copy=False)
    sample_approval_id = fields.Many2one('export.sample.approval', copy=False)
    bag_mark_id = fields.Many2one('export.bag.mark', copy=False)
    lc_id = fields.Many2one('export.lc', copy=False)
    cad_id = fields.Many2one('export.cad', copy=False)
    shipping_instruction_id = fields.Many2one('export.shipping.instruction', copy=False)
    booking_id = fields.Many2one('export.booking', copy=False)
    shipment_document_id = fields.Many2one('export.shipment.document', copy=False)
    nbe_settlement_id = fields.Many2one('export.nbe.settlement', copy=False)

    inspection_state = fields.Selection([
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ], string='Inspection Result', default='pending', tracking=True)

    picking_ids = fields.One2many('stock.picking', 'export_order_id', string='Deliveries')
    picking_count = fields.Integer(compute='_compute_picking_count')
    invoice_ids = fields.One2many('account.move', 'export_order_id', string='Invoices')
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    payment_count = fields.Integer(compute='_compute_payment_count')

    amount_due = fields.Monetary(compute='_compute_payment_amounts', store=True)
    amount_paid = fields.Monetary(compute='_compute_payment_amounts', store=True)
    balance = fields.Monetary(compute='_compute_payment_amounts', store=True)

    notes = fields.Html(string='Notes')

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        return [code for code, _label in EXPORT_STAGES if code != 'cancelled']

    @api.depends('state')
    def _compute_color(self):
        palette = {
            'quotation': 4, 'contract': 5, 'sample_approval': 3, 'bag_mark': 3,
            'payment_setup': 6, 'payment_process': 6, 'shipping_instruction': 2,
            'booking': 2, 'inspection': 8, 'shipment': 1, 'documentation': 9,
            'payment_collection': 10, 'nbe_settlement': 7, 'completed': 10,
            'cancelled': 1,
        }
        for rec in self:
            rec.color = palette.get(rec.state, 0)

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_ids)

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.depends('partner_id')
    def _compute_payment_count(self):
        Payment = self.env['account.payment']
        for rec in self:
            rec.payment_count = Payment.search_count([
                ('partner_id', '=', rec.partner_id.id),
                ('payment_type', '=', 'inbound'),
            ]) if rec.partner_id else 0

    @api.depends('invoice_ids.amount_total', 'invoice_ids.amount_residual')
    def _compute_payment_amounts(self):
        for rec in self:
            invoices = rec.invoice_ids.filtered(
                lambda m: m.move_type == 'out_invoice' and m.state == 'posted'
            )
            rec.amount_due = sum(invoices.mapped('amount_total'))
            rec.amount_paid = rec.amount_due - sum(invoices.mapped('amount_residual'))
            rec.balance = sum(invoices.mapped('amount_residual'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.export.order') or _('New')
        return super().create(vals_list)

    def _set_stage(self, stage):
        self.ensure_one()
        if self.state == 'cancelled':
            raise UserError(_('Cannot update a cancelled export order.'))
        self.state = stage

    def _ensure_child(self, model_name, field_name, vals=None):
        self.ensure_one()
        if getattr(self, field_name):
            return getattr(self, field_name)
        vals = dict(vals or {}, export_order_id=self.id)
        record = self.env[model_name].create(vals)
        self[field_name] = record.id
        return record

    # --- Phase 1: Quotation ---
    def action_send_quotation(self):
        for rec in self:
            if rec.sale_order_id.state == 'draft':
                rec.sale_order_id.action_quotation_send()
            rec.quotation_state = 'sent'

    def action_accept_quotation(self):
        for rec in self:
            if rec.quotation_state == 'rejected':
                raise UserError(_('This quotation was rejected.'))
            if rec.sale_order_id.state in ('draft', 'sent'):
                rec.sale_order_id.action_confirm()
            rec.quotation_state = 'accepted'
            rec._set_stage('contract')
            rec._ensure_child('export.contract', 'contract_id', {
                'partner_id': rec.partner_id.id,
                'sale_order_id': rec.sale_order_id.id,
            })

    def action_reject_quotation(self):
        for rec in self:
            rec.quotation_state = 'rejected'
            rec._set_stage('cancelled')
            if (
                not self.env.context.get('from_sale_order_cancel')
                and rec.sale_order_id.state in ('draft', 'sent')
            ):
                rec.sale_order_id.with_context(disable_cancel_warning=True).action_cancel()

    # --- Phase 2: Contract ---
    def action_prepare_contract(self):
        for rec in self:
            contract = rec._ensure_child('export.contract', 'contract_id', {
                'partner_id': rec.partner_id.id,
                'sale_order_id': rec.sale_order_id.id,
            })
            contract.action_prepare()

    def action_contract_complete(self):
        for rec in self:
            if not rec.contract_id or rec.contract_id.state != 'signed':
                raise UserError(_('Contract must be signed before continuing.'))
            rec._ensure_child('export.sample.approval', 'sample_approval_id', {
                'contract_id': rec.contract_id.id,
            })
            rec._ensure_child('export.bag.mark', 'bag_mark_id', {
                'contract_id': rec.contract_id.id,
            })
            rec._set_stage('sample_approval')

    # --- Phase 5 & 6-8: Payment ---
    def action_confirm_payment_setup(self):
        for rec in self:
            if not rec.export_payment_method:
                raise UserError(_('Set export payment method on the quotation.'))
            rec._set_stage('payment_process')
            if rec.export_payment_method == 'lc':
                rec._ensure_child('export.lc', 'lc_id', {'contract_id': rec.contract_id.id})
            elif rec.export_payment_method == 'cad':
                rec._ensure_child('export.cad', 'cad_id', {'contract_id': rec.contract_id.id})

    def action_validate_payment_process(self):
        for rec in self:
            if rec.export_payment_method == 'lc':
                if not rec.lc_id or rec.lc_id.state not in ('active', 'closed'):
                    raise UserError(_('LC must be active before continuing.'))
            elif rec.export_payment_method == 'cad':
                if not rec.cad_id or rec.cad_id.state != 'paid':
                    raise UserError(_('CAD payment must be collected before continuing.'))
            elif rec.export_payment_method == 'tt':
                if rec.balance > 0 and rec.amount_due > 0:
                    raise UserError(_('Collect before-shipment T/T payment via Accounting first.'))
            rec._ensure_child('export.shipping.instruction', 'shipping_instruction_id', {
                'contract_id': rec.contract_id.id,
            })
            rec._set_stage('shipping_instruction')

    # --- Phase 9-12: Logistics ---
    def action_confirm_shipping_instruction(self):
        for rec in self:
            si = rec.shipping_instruction_id
            if not si or si.state != 'confirmed':
                raise UserError(_('Shipping instruction must be confirmed.'))
            rec._ensure_child('export.booking', 'booking_id', {'contract_id': rec.contract_id.id})
            rec._set_stage('booking')

    def action_confirm_booking(self):
        for rec in self:
            if not rec.booking_id or rec.booking_id.state != 'confirmed':
                raise UserError(_('Shipping line booking must be confirmed.'))
            rec._set_stage('inspection')

    def action_pass_inspection(self):
        for rec in self:
            rec.inspection_state = 'passed'
            rec._set_stage('shipment')

    def action_fail_inspection(self):
        for rec in self:
            rec.inspection_state = 'failed'

    def action_confirm_shipment(self):
        for rec in self:
            if not rec.picking_ids.filtered(lambda p: p.state == 'done'):
                raise UserError(_('Complete at least one delivery/picking first.'))
            rec._ensure_child('export.shipment.document', 'shipment_document_id', {
                'contract_id': rec.contract_id.id,
            })
            rec._set_stage('documentation')

    # --- Phase 13-16: Documentation & settlement ---
    def action_confirm_documentation(self):
        for rec in self:
            doc = rec.shipment_document_id
            if not doc or doc.state != 'approved':
                raise UserError(_('Shipment documents must be approved.'))
            rec._set_stage('payment_collection')

    def action_confirm_final_payment(self):
        for rec in self:
            if rec.balance > 0:
                raise UserError(_('Outstanding balance must be cleared before NBE settlement.'))
            rec._ensure_child('export.nbe.settlement', 'nbe_settlement_id', {
                'contract_id': rec.contract_id.id,
                'export_value': rec.amount_total,
            })
            rec._set_stage('nbe_settlement')

    def action_complete_nbe(self):
        for rec in self:
            nbe = rec.nbe_settlement_id
            if not nbe or nbe.state != 'closed':
                raise UserError(_('NBE settlement must be closed.'))
            rec._set_stage('completed')

    # --- Accounting & inventory ---
    def action_create_invoice(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_('No quotation linked.'))
        invoices = self.sale_order_id._create_invoices()
        invoices.write({'export_order_id': self.id})
        return self.action_view_invoices()

    def action_create_delivery(self):
        self.ensure_one()
        order = self.sale_order_id
        if order.state not in ('sale', 'done'):
            raise UserError(_('Confirm the quotation before creating deliveries.'))
        if not order.picking_ids:
            raise UserError(
                _('No delivery available. Install/configure Sales Inventory (sale_stock) '
                  'and ensure products are storable.')
            )
        pickings = order.picking_ids.filtered(lambda p: p.state != 'cancel')
        pickings.write({'export_order_id': self.id})
        return self.action_view_pickings()

    # --- Navigation ---
    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quotation'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _open_child_form(self, record, name):
        if not record:
            raise UserError(_('Record not created yet for this stage.'))
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': record._name,
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_contract(self):
        return self._open_child_form(self.contract_id, _('Contract'))

    def action_view_sample_approval(self):
        return self._open_child_form(self.sample_approval_id, _('Sample Approval'))

    def action_view_bag_mark(self):
        return self._open_child_form(self.bag_mark_id, _('Bag Mark'))

    def action_view_lc(self):
        return self._open_child_form(self.lc_id, _('Letter of Credit'))

    def action_view_cad(self):
        return self._open_child_form(self.cad_id, _('CAD'))

    def action_view_shipping_instruction(self):
        return self._open_child_form(self.shipping_instruction_id, _('Shipping Instruction'))

    def action_view_booking(self):
        return self._open_child_form(self.booking_id, _('Booking'))

    def action_view_shipment_document(self):
        return self._open_child_form(self.shipment_document_id, _('Shipment Documents'))

    def action_view_nbe_settlement(self):
        return self._open_child_form(self.nbe_settlement_id, _('NBE Settlement'))

    def action_view_pickings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deliveries'),
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('export_order_id', '=', self.id)],
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('export_order_id', '=', self.id)],
        }

    def action_view_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Payments'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('payment_type', '=', 'inbound'),
            ],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
            },
        }

    def action_send_shipment_status(self):
        """Send shipment status email to customer."""
        template = self.env.ref(
            'export_process.mail_template_export_shipment_status',
            raise_if_not_found=False,
        )
        for rec in self:
            if template and rec.partner_id.email:
                template.send_mail(rec.id, force_send=True)
                rec.message_post(body=_('Shipment status email sent to customer.'))
            else:
                rec.message_post(body=_('Shipment status notification logged (no email template/customer email).'))
