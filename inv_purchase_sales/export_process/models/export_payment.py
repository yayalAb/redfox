# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ExportLc(models.Model):
    _name = 'export.lc'
    _description = 'Export Letter of Credit'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(default=lambda self: _('New'), copy=False)
    export_order_id = fields.Many2one('export.export.order', ondelete='cascade')
    contract_id = fields.Many2one('export.contract', string='Contract')
    lc_number = fields.Char(string='LC Number')
    issuing_bank = fields.Char()
    expiry_date = fields.Date()
    amount = fields.Monetary(currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('opened', 'Opened'),
        ('verified', 'Verified'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.lc') or _('New')
        return super().create(vals_list)

    def action_open(self):
        self.write({'state': 'opened'})

    def action_verify(self):
        self.write({'state': 'verified'})

    def action_activate(self):
        self.write({'state': 'active'})

    def action_close(self):
        self.write({'state': 'closed'})


class ExportCad(models.Model):
    _name = 'export.cad'
    _description = 'Export Cash Against Documents'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(default=lambda self: _('New'), copy=False)
    export_order_id = fields.Many2one('export.export.order', ondelete='cascade')
    contract_id = fields.Many2one('export.contract', string='Contract')
    document_sent_date = fields.Date()
    bank_reference = fields.Char()
    payment_received = fields.Boolean()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('documents_sent', 'Documents Sent'),
        ('awaiting_payment', 'Awaiting Payment'),
        ('paid', 'Paid'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.cad') or _('New')
        return super().create(vals_list)

    def action_send_documents(self):
        self.write({
            'document_sent_date': fields.Date.today(),
            'state': 'documents_sent',
        })

    def action_await_payment(self):
        self.write({'state': 'awaiting_payment'})

    def action_mark_paid(self):
        self.write({'payment_received': True, 'state': 'paid'})
