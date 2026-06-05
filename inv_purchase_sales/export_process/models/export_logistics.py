# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ExportShippingInstruction(models.Model):
    _name = 'export.shipping.instruction'
    _description = 'Export Shipping Instruction'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Instruction No.', default=lambda self: _('New'), copy=False)
    export_order_id = fields.Many2one('export.export.order', ondelete='cascade')
    contract_id = fields.Many2one('export.contract', string='Contract')
    shipping_date = fields.Date()
    port_loading = fields.Char(string='Port of Loading')
    port_discharge = fields.Char(string='Port of Discharge')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.shipping.instruction') or _('New')
        return super().create(vals_list)

    def action_request(self):
        self.write({'state': 'requested'})

    def action_confirm(self):
        self.write({'state': 'confirmed'})


class ExportBooking(models.Model):
    _name = 'export.booking'
    _description = 'Export Shipping Booking'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(default=lambda self: _('New'), copy=False)
    export_order_id = fields.Many2one('export.export.order', ondelete='cascade')
    contract_id = fields.Many2one('export.contract', string='Contract')
    shipping_line = fields.Char(string='Shipping Line')
    booking_number = fields.Char()
    vessel_name = fields.Char()
    etd = fields.Date(string='ETD')
    eta = fields.Date(string='ETA')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.booking') or _('New')
        return super().create(vals_list)

    def action_request(self):
        self.write({'state': 'requested'})

    def action_confirm(self):
        self.write({'state': 'confirmed'})
