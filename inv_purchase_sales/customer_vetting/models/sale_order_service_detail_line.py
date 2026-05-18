# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderServiceDetailLine(models.Model):
    _name = 'sale.order.service.detail.line'
    _description = 'Vetting detail (raw / bag) per service order line'
    _order = 'order_id, sequence, id'

    sequence = fields.Integer(default=10)
    order_id = fields.Many2one(
        'sale.order',
        string='Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    source_sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Service line',
        required=True,
        ondelete='cascade',
        index=True,
        domain="[]",
    )
    detail_type = fields.Selection(
        [
            ('other', 'Raw product'),
            ('bag', 'Bag'),
        ],
        string='Type',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('type', '!=', 'service')]",
    )
    name = fields.Text(string='Description')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    product_uom_qty = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        default=1.0,
    )

    _sql_constraints = [
        (
            'uniq_order_source_detail_type',
            'unique(order_id, source_sale_line_id, detail_type)',
            'Only one row of each type (Raw product / Bag) is allowed per service line on an order.',
        ),
    ]

    @api.constrains('source_sale_line_id', 'order_id')
    def _check_source_belongs_order(self):
        for line in self:
            if line.source_sale_line_id and line.order_id:
                if line.source_sale_line_id.order_id != line.order_id:
                    raise ValidationError(
                        _('The service line must belong to the same sales order.')
                    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.product_uom = line.product_id.uom_id
                if not line.name:
                    line.name = (
                        line.product_id.get_product_multiline_description_sale()
                        or line.product_id.display_name
                    )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if self.env.context.get('customer_vetting_skip_propagate_detail'):
            return lines
        propagate_keys = {
            'product_id',
            'product_uom',
            'product_uom_qty',
            'detail_type',
            'source_sale_line_id',
        }
        for line in lines:
            if line.order_id.service_request_id:
                line._customer_vetting_propagate_from_detail(propagate_keys)
        return lines

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('customer_vetting_skip_propagate_detail'):
            return res
        for line in self:
            if not line.order_id.service_request_id:
                continue
            line._customer_vetting_propagate_from_detail(set(vals.keys()))
        return res

    def _customer_vetting_propagate_from_detail(self, changed_keys):
        self.ensure_one()
        sol = self.source_sale_line_id
        if not sol or not self.product_id or not self.product_uom:
            return
        tmpl = sol.product_id.product_tmpl_id

        if self.detail_type == 'other':
            # Detail uses the *raw* product UoM; the service order line must keep
            # the *service* product UoM (same category as product_id on the SOL).
            if 'product_uom_qty' in changed_keys:
                sol.with_context(customer_vetting_skip_detail_reconcile=True).write({
                    'product_uom_qty': self.product_uom_qty,
                })
            if 'product_id' in changed_keys:
                tmpl.with_context(customer_vetting_skip_propagate_detail=True).write({
                    'vetting_other_product_id': self.product_id.product_tmpl_id.id,
                })
                self.order_id._sync_service_vetting_detail_lines()

        elif self.detail_type == 'bag':
            if 'product_id' in changed_keys:
                tmpl.with_context(customer_vetting_skip_propagate_detail=True).write({
                    'bag_id': self.product_id.product_tmpl_id.id,
                })
                self.order_id._sync_service_vetting_detail_lines()
