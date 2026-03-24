# -*- coding: utf-8 -*-
from odoo import models, fields


class LcLetterPaymentRequest(models.TransientModel):
    _name = 'lc.letter.payment.request'
    _description = 'LC Letter Payment Request'

    lc_letter_id = fields.Many2one(
        'lc.letter',
        string='LC Letter',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain=lambda self: self._get_product_domain(),
        help='Service products only. With stock_landed_costs, only products with Landed Cost enabled.',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
    )
    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        related='lc_letter_id.currency_id',
    )
    note = fields.Html(string='Note')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'lc_letter_payment_request_ir_attachment_rel',
        'payment_request_id',
        'attachment_id',
        string='Attachments',
    )

    def _get_product_domain(self):
        domain = [('type', '=', 'service')]
        if 'landed_cost_ok' in self.env['product.product']._fields:
            domain.append(('landed_cost_ok', '=', True))
        return domain

    def action_confirm(self):
        self.ensure_one()
        line_vals = {
            'product_id': self.product_id.id,
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'note': self.note or '',
            'state': 'submitted',
            'submitted_by': self.env.user.id,
        }
        new_line = self.env['lc.letter.payment.line'].create({
            **line_vals,
            'lc_letter_id': self.lc_letter_id.id,
        })
        if self.attachment_ids:
            new_line.attachment_ids = self.attachment_ids
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'lc.letter',
            'res_id': self.lc_letter_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
