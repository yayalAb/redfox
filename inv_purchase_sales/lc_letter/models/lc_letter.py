# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

PAYMENT_INSTRUMENTS = [
    ('lc', 'Letter of Credit'),
    ('cad', 'Cash Against Documents'),
    ('tt', 'Advance Payment (TT)'),
]

PAYMENT_SUBTYPES = [
    ('lc_confirmed', 'Confirmed LC'),
    ('lc_sight', 'LC at Sight'),
    ('lc_usance', 'LC at Acceptance / Usance / Deferred'),
    ('lc_transferable', 'Transferable LC'),
    ('cad_dp_sight', 'Document Against Payment (D/P) – Sight'),
    ('cad_da_usance', 'Document Against Acceptance (D/A) – Usance'),
    ('cad_partial_advance', 'Partial Advance + CAD'),
    ('tt_partial', 'Partial Advance Payment'),
    ('tt_full', 'Full Advance Payment'),
]

INSTRUMENT_SUBTYPES = {
    'lc': {'lc_confirmed', 'lc_sight', 'lc_usance', 'lc_transferable'},
    'cad': {'cad_dp_sight', 'cad_da_usance', 'cad_partial_advance'},
    'tt': {'tt_partial', 'tt_full'},
}

DEFAULT_SUBTYPE = {
    'lc': 'lc_sight',
    'cad': 'cad_dp_sight',
    'tt': 'tt_partial',
}

SEQUENCE_CODES = {
    'lc': 'lc.letter',
    'cad': 'lc.letter.cad',
    'tt': 'lc.letter.tt',
}


class LcLetter(models.Model):
    _name = 'lc.letter'
    _description = 'Foreign Payment Term'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(
        string='LC/Reference No.',
        required=True,
        copy=False,
        index=True,
        tracking=True,
    )
    payment_instrument = fields.Selection(
        selection=PAYMENT_INSTRUMENTS,
        string='Payment Instrument',
        required=True,
        default='lc',
        tracking=True,
    )
    payment_subtype = fields.Selection(
        selection='_selection_payment_subtype',
        string='Payment Type',
        required=True,
        default='lc_sight',
        tracking=True,
    )
    payment_reference_label = fields.Char(
        compute='_compute_payment_reference_label',
    )
    stage_id = fields.Many2one(
        'lc.letter.stage',
        string='Stage',
        required=True,
        index=True,
        tracking=True,
        copy=False,
        group_expand='_read_group_stage_ids',
        default=lambda self: self._default_stage_id(),
    )

    issuing_bank_id = fields.Many2one(
        'res.partner',
        string='Issuing Bank',
        domain=[('is_company', '=', True)],
        help='Bank that issues the Letter of Credit or processes the payment',
        tracking=True,
    )
    advising_bank_id = fields.Many2one(
        'res.partner',
        string='Advising Bank',
        domain=[('is_company', '=', True)],
        help='Bank that advises the LC to the beneficiary',
        tracking=True,
    )
    applicant_id = fields.Many2one(
        'res.partner',
        string='Applicant (Buyer)',
        required=True,
        domain=[('is_company', '=', True)],
        tracking=True,
    )
    beneficiary_id = fields.Many2one(
        'res.partner',
        string='Beneficiary (Seller)',
        required=True,
        domain=[('is_company', '=', True)],
        tracking=True,
    )

    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id',
        tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )

    issue_date = fields.Date(string='Issue Date', tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    latest_shipment_date = fields.Date(
        string='Latest Shipment Date', tracking=True)

    lc_type = fields.Selection([
        ('sight', 'Sight LC'),
        ('usance', 'Usance/Time LC'),
        ('revocable', 'Revocable'),
        ('irrevocable', 'Irrevocable'),
    ], string='LC Banking Type', default='irrevocable', tracking=True)

    description = fields.Text(string='Description', tracking=True)
    notes = fields.Html(string='Internal Notes')

    payment_line_ids = fields.One2many(
        'lc.letter.payment.line',
        'lc_letter_id',
        string='Payment Lines',
    )
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'lc_letter_id',
        string='Purchase Orders',
    )
    purchase_order_count = fields.Integer(
        string='Purchase Order Count',
        compute='_compute_purchase_order_count',
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        tracking=True,
    )

    @api.model
    def _selection_payment_subtype(self):
        return PAYMENT_SUBTYPES

    @api.depends('payment_instrument')
    def _compute_payment_reference_label(self):
        labels = {
            'lc': _('LC No'),
            'cad': _('CAD Ref'),
            'tt': _('TT Ref'),
        }
        for rec in self:
            rec.payment_reference_label = labels.get(
                rec.payment_instrument, _('Reference No'))

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for rec in self:
            rec.purchase_order_count = len(rec.purchase_order_ids)

    @api.onchange('payment_instrument')
    def _onchange_payment_instrument(self):
        if self.payment_instrument:
            self.payment_subtype = DEFAULT_SUBTYPE.get(self.payment_instrument)
        if self.payment_instrument != 'lc':
            self.lc_type = False
            if self.payment_instrument == 'tt':
                self.issuing_bank_id = False
                self.advising_bank_id = False
                self.expiry_date = False

    @api.constrains('payment_instrument', 'payment_subtype')
    def _check_payment_subtype(self):
        for rec in self:
            allowed = INSTRUMENT_SUBTYPES.get(rec.payment_instrument, set())
            if rec.payment_subtype and rec.payment_subtype not in allowed:
                raise ValidationError(_(
                    'Payment type "%(subtype)s" is not valid for %(instrument)s.',
                    subtype=dict(PAYMENT_SUBTYPES).get(rec.payment_subtype),
                    instrument=dict(PAYMENT_INSTRUMENTS).get(rec.payment_instrument),
                ))

    @api.constrains('payment_instrument', 'expiry_date')
    def _check_expiry_date(self):
        for rec in self:
            if rec.payment_instrument == 'lc' and not rec.expiry_date:
                raise ValidationError(_(
                    'Expiry date is required for Letter of Credit documents.'))

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('lc_letter_id', '=', self.id)],
            'context': {
                'default_lc_letter_id': self.id,
                'default_x_payment_term_foreign': self.payment_instrument,
            },
        }

    @api.model
    def _default_stage_id(self):
        return self.env['lc.letter.stage'].search([], order='sequence asc', limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None):
        return stages.search([], order=order or stages._order)

    def _get_sequence_code(self, payment_instrument=None):
        instrument = payment_instrument or self.payment_instrument or 'lc'
        return SEQUENCE_CODES.get(instrument, 'lc.letter')

    @api.model
    def _generate_reference_name(self, payment_instrument=None):
        instrument = payment_instrument or 'lc'
        seq_code = SEQUENCE_CODES.get(instrument, 'lc.letter')
        return self.env['ir.sequence'].next_by_code(seq_code) or _('New')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            instrument = vals.get('payment_instrument') or 'lc'
            if not vals.get('payment_subtype'):
                vals['payment_subtype'] = DEFAULT_SUBTYPE.get(instrument, 'lc_sight')
            name = (vals.get('name') or '').strip()
            if not name or name == 'New':
                vals['name'] = self._generate_reference_name(instrument)
        return super().create(vals_list)

    def action_payment_request(self):
        self.ensure_one()
        return {
            'name': 'Payment Request',
            'type': 'ir.actions.act_window',
            'res_model': 'lc.letter.payment.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lc_letter_id': self.id},
        }
