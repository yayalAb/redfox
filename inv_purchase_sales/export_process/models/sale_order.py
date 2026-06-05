# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    _EXPORT_PAYMENT_VALUES = frozenset({'lc', 'cad', 'tt'})

    sale_scope = fields.Selection(
        [
            ('local', 'Local'),
            ('foreign', 'Foreign'),
        ],
        string='Sale Scope',
        default='local',
        required=True,
        tracking=True,
    )
    destination_country_id = fields.Many2one(
        'res.country',
        string='Destination Country',
        tracking=True,
    )
    incoterm_id = fields.Many2one(
        'account.incoterms',
        string='Incoterm',
        tracking=True,
    )
    export_payment_method = fields.Selection(
        [
            ('lc', 'Letter of Credit'),
            ('cad', 'Cash Against Document'),
            ('tt', 'Telegraphic Transfer'),
        ],
        string='Export Payment Method',
        tracking=True,
    )
    export_order_id = fields.Many2one(
        'export.export.order',
        string='Export Order',
        copy=False,
    )
    export_order_count = fields.Integer(compute='_compute_export_order_count')
    export_order_state = fields.Selection(
        related='export_order_id.state',
        string='Export Stage',
        store=True,
    )

    def _compute_export_order_count(self):
        for order in self:
            order.export_order_count = 1 if order.export_order_id else 0

    def _split_export_payment_method(self, vals):
        """Route LC/CAD/TT away from stock_picking_custom payment_method (cash/credit)."""
        payment_method = vals.get('payment_method')
        if payment_method in self._EXPORT_PAYMENT_VALUES:
            vals['export_payment_method'] = payment_method
            vals.pop('payment_method', None)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._split_export_payment_method(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._split_export_payment_method(vals)
        return super().write(vals)

    @api.constrains('sale_scope', 'export_order_id')
    def _check_foreign_export_order(self):
        for order in self:
            if order.export_order_id and order.sale_scope != 'foreign':
                raise UserError(
                    _('Export orders are only allowed for foreign quotations.')
                )

    def action_start_export_order(self):
        self.ensure_one()
        if self.export_order_id:
            return self.action_view_export_order()
        if not self.partner_id:
            raise UserError(_('Select a customer before starting the export order.'))
        if not self.order_line.filtered(lambda l: not l.display_type):
            raise UserError(_('Add at least one product line to the quotation first.'))
        if self.state not in ('draft', 'sent'):
            raise UserError(
                _('Export order can only be started from a draft or sent quotation.')
            )
        if self.sale_scope != 'foreign':
            raise UserError(
                _('Export order can only be started for foreign quotations. '
                  'Set Sale Scope to Foreign first.')
            )

        export_order = self.env['export.export.order'].create({
            'sale_order_id': self.id,
            'export_payment_method': self.export_payment_method,
            'quotation_state': 'sent' if self.state == 'sent' else 'draft',
        })
        self.export_order_id = export_order.id
        export_order.message_post(
            body=_('Export order started from quotation %s.') % self.name,
        )
        return self.action_view_export_order()

    def action_view_export_order(self):
        self.ensure_one()
        if not self.export_order_id:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'name': _('Export Order'),
            'res_model': 'export.export.order',
            'res_id': self.export_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _action_cancel(self):
        for order in self:
            export = order.export_order_id
            if export and export.state not in ('completed', 'cancelled'):
                export.with_context(from_sale_order_cancel=True).action_reject_quotation()
        return super()._action_cancel()
