# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ExportShipmentDocument(models.Model):
    _name = 'export.shipment.document'
    _description = 'Export Shipment Documents'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(default=lambda self: _('New'), copy=False)
    export_order_id = fields.Many2one('export.export.order', ondelete='cascade')
    contract_id = fields.Many2one('export.contract', string='Contract')
    commercial_invoice = fields.Binary(attachment=True)
    commercial_invoice_filename = fields.Char()
    packing_list = fields.Binary(attachment=True)
    packing_list_filename = fields.Char()
    certificate_origin = fields.Binary(string='Certificate of Origin', attachment=True)
    certificate_origin_filename = fields.Char()
    bill_of_lading = fields.Binary(attachment=True)
    bill_of_lading_filename = fields.Char()
    inspection_certificate = fields.Binary(attachment=True)
    inspection_certificate_filename = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('reviewed', 'Reviewed'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.shipment.document') or _('New')
        return super().create(vals_list)

    def action_review(self):
        self.write({'state': 'reviewed'})

    def action_send(self):
        self.write({'state': 'sent'})

    def action_approve(self):
        self.write({'state': 'approved'})


class ExportNbeSettlement(models.Model):
    _name = 'export.nbe.settlement'
    _description = 'Export NBE Settlement'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(default=lambda self: _('New'), copy=False)
    export_order_id = fields.Many2one('export.export.order', ondelete='cascade')
    contract_id = fields.Many2one('export.contract', string='Contract')
    export_value = fields.Monetary(currency_field='currency_id')
    received_forex = fields.Monetary(string='Received Forex', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    bank_name = fields.Char()
    settlement_date = fields.Date()
    nbe_reference = fields.Char(string='NBE Reference')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('closed', 'Closed'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.nbe.settlement') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_close(self):
        self.write({'state': 'closed'})
