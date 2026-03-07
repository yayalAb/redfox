# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaymentRequest(models.Model):
    _name = 'payment.request'
    _description = 'Payment Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=False, 
                       default=lambda self: _('New'))
    
    # Linked Documents
    sale_order_id = fields.Many2one('sale.order', string='Source Sale Order', required=False, readonly=False) 
    partner_id = fields.Many2one('res.partner', related='sale_order_id.partner_id', string='Customer', store=True, readonly=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='sale_order_id.currency_id')
    
    # Contract Link
    agreement_id = fields.Many2one('sale.agreement', string="Contract / PO Ref", required=False, readonly=False)

    # General Info
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    department_name = fields.Char(string='Department') 

    # Content Fields
    subject = fields.Char(string='Subject', default='Payment Request for Product Sales')
    header_text = fields.Text(string='Header Text', 
                              default="Pursuant to the above referred purchase order No.Wagwago Trading Plc hereby request payment amount for the items ")
    contract_ref_text = fields.Char(
        string="Contract Reference Line",
        help="The line appearing above Subject, e.g., Ref: purchase orders No...", required=False,
        tracking=True
    )

    # Bank Details HTML Field (Flexible Table)
    bank_details_html = fields.Html(
        string='Bank Details',
        default="""
            <table class="table table-bordered table-sm">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th class="text-center" style="width: 10%;">S/N</th>
                        <th style="width: 40%;">Account Name</th>
                        <th style="width: 50%;">Account Detail</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="text-center">1</td>
                        <td>Telebirr</td>
                        <td>
                            <strong>Account Title:</strong> Wagwago Trading Plc<br/>
                            <strong>Account No:</strong> 731563
                        </td>
                    </tr>
                </tbody>
            </table>
        """,
        help="Editable table for bank accounts."
    )

    # Note: I removed the single bank fields (account_name, account_title, bank_account_number) 
    # because you are using the HTML table now. If you still need them for legacy support, keep them, 
    # but the report uses the HTML field.

    line_ids = fields.One2many('payment.request.line', 'request_id', string='Request Lines')
    amount_total = fields.Monetary(string='Total Amount', compute='_compute_total', store=True)

    # Purchase Request Link
    purchase_request_ids = fields.One2many('purchase.request', 'payment_request_id', string='Purchase Requests')
    purchase_request_count = fields.Integer(string="Purchase Request Count", compute='_compute_purchase_request_count')

    # Approval Capture
    approver_id = fields.Many2one('res.users', string="Approved By", readonly=True, copy=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status', tracking=True)

    # --- COMPUTE & ONCHANGE METHODS ---

    @api.depends('line_ids.total_price')
    def _compute_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('total_price'))

    @api.depends('purchase_request_ids')
    def _compute_purchase_request_count(self):
        for rec in self:
            rec.purchase_request_count = len(rec.purchase_request_ids)

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if not self.sale_order_id:
            return

        # Auto-fill Customer
        self.partner_id = self.sale_order_id.partner_id
        
        # Auto-fill Contract
        if hasattr(self.sale_order_id, 'agreement_id') and self.sale_order_id.agreement_id:
            self.agreement_id = self.sale_order_id.agreement_id
            self._onchange_agreement_id() 

        # Auto-fill Product Lines
        new_lines = [(5, 0, 0)] # Clear existing
        for line in self.sale_order_id.order_line:
            if not line.display_type:
                new_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.product_uom_qty,
                    'uom_id': line.product_uom.id,
                    'price_unit': line.price_unit,
                }))
        self.line_ids = new_lines
        
    @api.onchange('agreement_id')
    def _onchange_agreement_id(self):
        if self.agreement_id:
            ref_date = self.agreement_id.signature_date or self.agreement_id.start_date or fields.Date.today()
            ref_no = self.agreement_id.code or "N/A"
            ref_name = self.agreement_id.name or ""
            self.contract_ref_text = f"Ref: purchase orders No: {ref_no} Dated {ref_date} {ref_name}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('payment.request') or _('New')
        return super().create(vals_list)

    # --- WORKFLOW ACTIONS ---

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Only draft requests can be submitted."))
            rec.state = 'submitted'

    def action_review(self):
        for rec in self:
            if rec.state != 'submitted':
                raise ValidationError(_("Request must be Submitted before Review."))
            rec.state = 'review'

    def action_approve(self):
        for rec in self:
            if rec.state != 'review':
                raise ValidationError(_("Request must be Reviewed before Approval."))
            
            # Capture the approver
            rec.approver_id = self.env.user
            rec.state = 'approved'

    def action_send_email(self):
        self.ensure_one()
        if self.state not in ['approved', 'sent', 'paid']:
             raise ValidationError(_("You must Approve the request before sending it."))
        
        if self.state == 'approved':
            self.state = 'sent'
        
        template_id = self.env.ref('custom_sale_agreement.email_template_payment_request', raise_if_not_found=False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        
        ctx = dict(
            default_model='payment.request',
            default_res_ids=[self.id],
            default_use_template=bool(template_id),
            default_template_id=template_id and template_id.id or False,
            default_composition_mode='comment',
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def action_print(self):
        self.ensure_one()
        if self.state not in ['approved', 'sent', 'paid']:
            raise ValidationError(_("You cannot print the request until it is Approved."))
        
        if self.state == 'approved':
            self.state = 'sent'
            
        return self.env.ref('custom_sale_agreement.action_report_payment_request').report_action(self)

    def action_mark_paid(self):
        for rec in self:
            if rec.state != 'sent':
                raise ValidationError(_("Only Sent requests can be marked as Paid."))
            rec.state = 'paid'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    # --- LINKED ACTIONS ---

    def action_view_purchase_requests(self):
        self.ensure_one()
        return {
            'name': _('Purchase Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request',
            'view_mode': 'list,form',
            'domain': [('payment_request_id', '=', self.id)],
            'context': {'default_payment_request_id': self.id}
        }

    def action_create_purchase_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Purchase Request',
            'res_model': 'purchase.request',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_payment_request_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_name': 'New',
            }
        }


class PaymentRequestLine(models.Model):
    _name = 'payment.request.line'
    _description = 'Payment Request Line'

    request_id = fields.Many2one('payment.request', string='Request')
    name = fields.Text(string='Description', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Qty', default=1.0)
    uom_id = fields.Many2one('uom.uom', string='UoM')
    price_unit = fields.Float(string='Unit Price')
    total_price = fields.Float(string='Total Price', compute='_compute_total')
    currency_id = fields.Many2one('res.currency', related='request_id.currency_id')

    @api.depends('quantity', 'price_unit')
    def _compute_total(self):
        for line in self:
            line.total_price = line.quantity * line.price_unit