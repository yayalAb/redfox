# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    service_request_id = fields.Many2one(
        'service.request',
        string='Service request',
        ondelete='set null',
        copy=False,
        index=True,
    )
    vetting_detail_line_ids = fields.One2many(
        comodel_name='sale.order.service.detail.line',
        inverse_name='order_id',
        string='Product vetting details',
        copy=False,
    )

    def _primary_template_variant(self, template):
        """Return one product.product for a template (or empty recordset)."""
        if not template:
            return self.env['product.product']
        if template.product_variant_id:
            return template.product_variant_id
        return template.product_variant_ids[:1]

    def _sync_service_vetting_detail_lines(self):
        Detail = self.env['sale.order.service.detail.line']
        for order in self:
            if not order.service_request_id:
                order.vetting_detail_line_ids.unlink()
                continue

            service_lines = order.order_line.filtered(
                lambda l: not l.display_type and l.product_id and l.product_id.type == 'service'
            )
            desired = set()
            sequence = 0

            for sol in service_lines:
                tmpl = sol.product_id.product_tmpl_id

                for dtype, sub_tmpl in (
                    ('other', tmpl.vetting_other_product_id),
                    ('bag', tmpl.bag_id),
                ):
                    if not sub_tmpl:
                        continue
                    variant = order._primary_template_variant(sub_tmpl)
                    if not variant:
                        continue

                    desired.add((sol.id, dtype))
                    sequence += 10
                    desc = variant.get_product_multiline_description_sale() or variant.display_name
                    existing = Detail.search(
                        [
                            ('order_id', '=', order.id),
                            ('source_sale_line_id', '=', sol.id),
                            ('detail_type', '=', dtype),
                        ],
                        limit=1,
                    )

                    if dtype == 'other':
                        vals = {
                            'sequence': sequence,
                            'product_id': variant.id,
                            'product_uom': sol.product_uom.id,
                            'product_uom_qty': sol.product_uom_qty,
                        }
                        if not existing or existing.product_id != variant:
                            vals['name'] = desc
                    else:
                        if existing:
                            vals = {'sequence': sequence}
                            if existing.product_id != variant:
                                vals['product_id'] = variant.id
                                vals['name'] = desc
                        else:
                            vals = {
                                'sequence': sequence,
                                'product_id': variant.id,
                                'name': desc,
                                'product_uom': variant.uom_id.id,
                                'product_uom_qty': 1.0,
                            }

                    if existing:
                        existing.with_context(customer_vetting_skip_propagate_detail=True).write(
                            vals
                        )
                    else:
                        Detail.create(
                            {
                                **vals,
                                'order_id': order.id,
                                'source_sale_line_id': sol.id,
                                'detail_type': dtype,
                            }
                        )

            orphans = order.vetting_detail_line_ids.filtered(
                lambda d: (d.source_sale_line_id.id, d.detail_type) not in desired
            )
            orphans.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._sync_service_vetting_detail_lines()
        return orders

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('order_line', 'service_request_id')):
            self._sync_service_vetting_detail_lines()
        return res

    _sql_constraints = [
        (
            'customer_vetting_service_request_unique',
            'unique(service_request_id)',
            'Each service request can only be linked to one sales order.',
        ),
    ]
