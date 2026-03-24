# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    purchase_origin = fields.Selection([
        ('local', 'Local'), ('foreign', 'Foreign')],
        string='Purchase Type')


class LcLetter(models.Model):
    _name = 'lc.letter'
    _description = 'Letter of Credit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(
        string='LC Number',
        required=True,
        copy=False,
        index=True,
        default='New',
        tracking=True,
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
        help='Bank that issues the Letter of Credit',
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
    expiry_date = fields.Date(string='Expiry Date',
                              required=True, tracking=True)
    latest_shipment_date = fields.Date(
        string='Latest Shipment Date', tracking=True)

    lc_type = fields.Selection([
        ('sight', 'Sight LC'),
        ('usance', 'Usance/Time LC'),
        ('revocable', 'Revocable'),
        ('irrevocable', 'Irrevocable'),
    ], string='LC Type', default='irrevocable', tracking=True)

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

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for rec in self:
            rec.purchase_order_count = len(rec.purchase_order_ids)

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('lc_letter_id', '=', self.id)],
            'context': {'default_lc_letter_id': self.id},
        }

    @api.model
    def _default_stage_id(self):
        return self.env['lc.letter.stage'].search([], order='sequence asc', limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None):
        return stages.search([], order=order or stages._order)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'lc.letter') or 'New'
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
