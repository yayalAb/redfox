# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ExportContract(models.Model):
    _name = 'export.contract'
    _description = 'Export Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(default=lambda self: _('New'), copy=False)
    export_order_id = fields.Many2one('export.export.order', ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', string='Quotation')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    contract_date = fields.Date(default=fields.Date.today)
    contract_file = fields.Binary(string='Contract File', attachment=True)
    contract_filename = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('prepared', 'Prepared'),
        ('sent', 'Sent'),
        ('signed', 'Signed'),
    ], default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('export.contract') or _('New')
        return super().create(vals_list)

    def action_prepare(self):
        self.write({'state': 'prepared'})

    def action_send(self):
        self.write({'state': 'sent'})

    def _get_linked_export_order(self):
        self.ensure_one()
        if self.export_order_id:
            return self.export_order_id
        if self.sale_order_id and self.sale_order_id.export_order_id:
            return self.sale_order_id.export_order_id
        return self.env['export.export.order']

    def action_sign(self):
        self.write({'state': 'signed'})
        for rec in self:
            export_order = rec._get_linked_export_order()
            if not export_order:
                continue
            if not rec.export_order_id:
                rec.export_order_id = export_order.id
            if export_order.state == 'contract':
                if export_order.contract_id != rec:
                    export_order.contract_id = rec.id
                export_order.action_contract_complete()
            export_order.message_post(
                body=_('Contract %s signed.') % rec.name,
            )
