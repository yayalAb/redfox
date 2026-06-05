# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ExportSampleApproval(models.Model):
    _name = 'export.sample.approval'
    _description = 'Export Sample Approval'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(default=lambda self: _('New'), copy=False)
    export_order_id = fields.Many2one('export.export.order', ondelete='cascade')
    contract_id = fields.Many2one('export.contract', string='Contract')
    sample_reference = fields.Char(string='Sample Reference')
    sent_date = fields.Date()
    approved_date = fields.Date()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.sample.approval') or _('New')
        return super().create(vals_list)

    def action_send(self):
        self.write({'sent_date': fields.Date.today(), 'state': 'sent'})

    def action_approve(self):
        self.write({'approved_date': fields.Date.today(), 'state': 'approved'})
        for rec in self:
            order = rec.export_order_id
            if order and order.state == 'sample_approval':
                order._set_stage('bag_mark')

    def action_reject(self):
        self.write({'state': 'rejected'})


class ExportBagMark(models.Model):
    _name = 'export.bag.mark'
    _description = 'Export Bag Mark Approval'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(default=lambda self: _('New'), copy=False)
    export_order_id = fields.Many2one('export.export.order', ondelete='cascade')
    contract_id = fields.Many2one('export.contract', string='Contract')
    attachment = fields.Binary(string='Bag Mark File', attachment=True)
    attachment_filename = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.bag.mark') or _('New')
        return super().create(vals_list)

    def action_send(self):
        self.write({'state': 'sent'})

    def action_approve(self):
        self.write({'state': 'approved'})
        for rec in self:
            order = rec.export_order_id
            if order and order.state == 'bag_mark':
                order._set_stage('payment_setup')

    def action_reject(self):
        self.write({'state': 'rejected'})
