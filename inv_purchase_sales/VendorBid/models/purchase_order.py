from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
import re
from math import modf

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    rfp_id = fields.Many2one(
        'supplies.rfp', string='RP', index=True, copy=False)
    purchase_origin = fields.Selection([
        ('local', 'Local'), ('foreign', 'Foreign')],
        string='Purchase Type')
    final_po = fields.Boolean(string="Final PO", default=False)

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('submit', 'Submitted'),
        ('to approve', 'Verified'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', index=True, copy=False, default='draft', tracking=True)

    submitted_by = fields.Many2one(
        'res.users', string='Submitted by', copy=False, tracking=True)
    verified_by = fields.Many2one(
        'res.users', string='Verified by', copy=False, tracking=True)
    approved_by = fields.Many2one(
        'res.users', string='Approved by', copy=False, trancking=True)

    # Foriegn purchases related fields
    payment_term = fields.Selection(
        [('lc', 'L/C'), ('tt', 'TT'), ('cad', 'CAD')])
    country_origin = fields.Char(string='Country of Origin')
    good_description = fields.Char(string='Description of Goods')
    supplier_pi_number = fields.Char(string='Suppliers PI number')
    port_loading = fields.Char(string='Port Loading')
    port_discharge = fields.Char(string='Port Discharge')
    final_destination = fields.Char(string='Final Destination')
    bank_name = fields.Char(string='Vendor Bank Name')
    bank_address = fields.Char(string='Vendor Bank Address')
    swift_code = fields.Char(string='Vendor Swift Code')
    account_number = fields.Char(string='Vendor Account Number')

    warranty_period = fields.Integer(string='Warrenty Period (in months)')
    validity_period = fields.Date(string='Validity Period')
    applied_tax_ids = fields.Many2many(
        'account.tax',
        string='Applied Taxes',
        domain=[('type_tax_use', '=', 'purchase')],
        help='Select taxes to apply to all order lines'
    )
    price_tax_included = fields.Boolean(
        string='Price Tax Included',
        default=False,
        help='If checked, prices include taxes'
    )
    foreign_document_ids = fields.One2many(
        'purchase.order.document',
        'purchase_order_id',
        string='Foreign Purchase Documents'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('purchase_origin') == 'foreign' and vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'purchase.order.foreign') or _('New')
        return super().create(vals_list)

    def _approval_allowed(self):
        """Returns whether the order qualifies to be approved by the current user"""
        self.ensure_one()
        return (
            self.company_id.po_double_validation == 'one_step'
            or (self.company_id.po_double_validation == 'two_step'
                and self.amount_total < self.env.company.currency_id._convert(
                    self.company_id.po_double_validation_amount, self.currency_id, self.company_id,
                    self.date_order or fields.Date.today()))
            or self.env.user.has_group('purchase.group_purchase_manager'))

    @api.onchange('applied_tax_ids')
    def _onchange_applied_tax_ids(self):
        """Apply selected taxes to all order lines"""
        if self.applied_tax_ids:
            for line in self.order_line:
                line.taxes_id = self.applied_tax_ids

    def _compute_amount_all(self):
        """Override to exclude out of stock/out of specification lines from price comparison"""
        super()._compute_amount_all()
        for order in self:
            # Recalculate amounts excluding out of stock/out of specification lines
            lines_without_out_of_stock = order.order_line.filtered(
                lambda l: not l.out_of_stock
            )
            if lines_without_out_of_stock:
                order.amount_untaxed = sum(
                    lines_without_out_of_stock.mapped('price_subtotal'))
                # Recalculate tax for lines without out of stock
                order.amount_tax = sum(
                    lines_without_out_of_stock.mapped('price_tax'))
                order.amount_total = order.amount_untaxed + order.amount_tax
            else:
                # If all lines are out of stock, set amounts to 0
                order.amount_untaxed = 0.0
                order.amount_tax = 0.0
                order.amount_total = 0.0

    def action_submit(self):
        for rec in self:
            rec.write({'state': 'submit', 'submitted_by': self.env.user.id})

    def button_approve(self, force=False):
        self = self.filtered(lambda order: order._approval_allowed())
        self.write({'state': 'purchase', 'date_approve': fields.Datetime.now(
        ), 'approved_by': self.env.user.id})
        self.filtered(lambda p: p.company_id.po_lock ==
                      'lock').write({'state': 'done'})
        return {}

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'submit']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            # if order._approval_allowed():
            #     order.button_approve()
            # else:
            order.write(
                {'state': 'to approve', 'verified_by': self.env.user.id})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    @api.model
    def format_amount_to_text(self, amount, currency):
        """
        Format amount to text forcing 2-digit cents and minimizing 'and'.
        """

        if not currency:
            return str(amount)

        try:
            amount = float(amount)
            cents_value, int_value = modf(round(amount, 2))
            int_value = int(int_value)
            cents_value = int(round(cents_value * 100))  # e.g. 0.28 -> 28
        except Exception as e:
            _logger.error(
                "format_amount_to_text: Error converting amount: %s", e)
            return str(amount)

        _logger.debug(
            "format_amount_to_text: Int Part: %s, Cents Part: %s", int_value, cents_value)

        # 2. LOGIC CHANGE: Generate text for Integer and Cents separately.
        # This bypasses Odoo's internal logic that might try to read 4 decimal places.

        # A. Get text for the main integer part (e.g. "Four Hundred Dollars")
        # Note: We use the currency to generate this, but we will strip the trailing cents/zeros later
        int_text_raw = currency.amount_to_text(int_value)

        # B. Get text for the cents part by treating it as a whole number (e.g. 28 -> "Twenty Eight")
        # We temporarily generate text for '28 Dollars' then strip 'Dollars'
        cents_text_raw = currency.amount_to_text(cents_value)

        # Pattern to identify currency words (User's pattern)
        currency_pattern = r'\s+(Birr|Dollar|Pound|Euro|Yen|Yuan|Rupee|Peso|Krone|Franc|Lira|Ruble|Won|Baht|Ringgit|Dinar|Dirham|Riyal|Shekel|Rial|Taka|Kyat|Riel|Kip|Dong|Rupiah|Tugrik|Som|Tenge|Manat|Lari|Dram|Lek|Mark|Lev|Kuna|Zloty|Koruna|Forint|Leu|Lei|Denar|Shekel|Rial|Ringgit|Baht|Won|Ruble|Lira|Franc|Krone|Peso|Rupee|Yuan|Yen|Euro|Pound|Dollar|Birr)'

        # 3. Clean and Extract Integer Text
        match_int = re.search(currency_pattern, int_text_raw, re.IGNORECASE)
        if match_int:
            # Keep everything up to the end of the currency name
            # e.g. "Four Hundred Dollars and Zero Cents" -> "Four Hundred Dollars"
            main_part = int_text_raw[:match_int.end()]
        else:
            main_part = int_text_raw  # Fallback

        # 4. Clean and Extract Cents Text
        # We need to extract just the words "Twenty Eight" from "Twenty Eight Dollars..."
        match_cents = re.search(
            currency_pattern, cents_text_raw, re.IGNORECASE)
        if match_cents:
            # Take part BEFORE the currency name
            cents_word_part = cents_text_raw[:match_cents.start()]
        else:
            cents_word_part = str(cents_value)  # Fallback

        # 5. Combine them manually
        # This forces the format: "X Dollars and Y Cents"
        # We assume the subunit is "Cents". If you need "Santeem" for Birr, you can add logic here.
        subunit_name = "Cents"
        if currency.name == 'ETB':  # Optional: Custom subunit for Birr
            subunit_name = "Cents"  # or Santeem if preferred

        amount_text = f"{main_part} and {cents_word_part} {subunit_name}"

        # 6. Apply your cleanup logic (Removing excessive 'And')
        # We apply this to the WHOLE string now

        # Clean "Hundred And" -> "Hundred"
        amount_text = re.sub(r'\bHundred\s+And\s+', 'Hundred ',
                             amount_text, flags=re.IGNORECASE)

        # Remove "Thousand And", "Million And"
        amount_text = re.sub(r'\b(Thousand|Million|Billion|Trillion)\s+And\s+',
                             r'\1 ', amount_text, flags=re.IGNORECASE)

        # Clean up multiple spaces
        amount_text = re.sub(r'\s+', ' ', amount_text)

        # Clean up spaces around commas
        amount_text = re.sub(r'\s*,\s*', ', ', amount_text)

        # Capitalize first letter
        if amount_text:
            amount_text = amount_text[0].upper(
            ) + amount_text[1:] if len(amount_text) > 1 else amount_text.upper()

        _logger.info("format_amount_to_text: Final Result: '%s'",
                     amount_text.strip())

        return amount_text.strip()


class PurchaseOrderDocument(models.Model):
    _name = 'purchase.order.document'
    _description = 'Foreign Purchase Attachment'

    document_type = fields.Selection([
        ('currency_approval', 'Foreign Currency Approval'),
        ('esw_app', 'ESW Application'),
        ('insurance', 'Insurance Payment'),
        ('lc_opening', 'LC Opening'),
        ('document_collection', 'Document Collection'),
        ('tax_asset', 'Tax Asset'),
        ('tax_guarantee', 'Tax Payment and Guarantee'),
        ('customs_clearance', 'Customs Clearance')
    ], string='Document Type', required=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order Reference', ondelete='cascade')
    attachement = fields.Binary(string='Attachment',)
    file_name = fields.Char(string='File Name')
    attached_by = fields.Many2one(
        'res.users',
        string='Attached By',
        readonly=True,
        tracking=True,
        default=lambda self: self.env.user.id
    )
    state = fields.Selection([
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('done', 'Done')
    ], string='Status', default='pending', tracking=True, readonly=True)

    _sql_constraints = [
        ('unique_document_type_per_rfp',
         'unique(rfp_id, document_type)',
         'This document type has already been added to this Purchase Request!')
    ]

    def action_review_doc(self):
        self.write({'state': 'reviewed'})

    def action_done_doc(self):
        self.write({'state': 'done'})
