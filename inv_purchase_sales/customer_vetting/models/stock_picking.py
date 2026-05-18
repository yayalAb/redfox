# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    customer_vetting_product_detail_receipt = fields.Boolean(
        string='Product detail vetting receipt',
        compute='_compute_customer_vetting_product_detail_receipt',
        store=True,
        help='Technical: used to keep weighbridge line fields editable after validation.',
    )
    customer_vetting_sale_id = fields.Many2one(
        'sale.order',
        string='Sales order (product detail receipt)',
        ondelete='set null',
        copy=False,
        index=True,
    )
    customer_vetting_cdn_required_filtering_quality = fields.Float(
        string='Required filtering quality (CDN)',
        compute='_compute_customer_vetting_cdn_required_filtering_quality',
        digits=(16, 4),
        help='Sale order required filtering quality for delivery note printout.',
    )

    @api.depends(
        'customer_vetting_sale_id',
        'customer_vetting_sale_id.required_filtering_quality',
        'origin',
        'company_id',
    )
    def _compute_customer_vetting_cdn_required_filtering_quality(self):
        for picking in self:
            order = picking.customer_vetting_sale_id
            if not order:
                order = picking._customer_vetting_product_detail_receipt_sale_order()
            picking.customer_vetting_cdn_required_filtering_quality = (
                (order.required_filtering_quality or 0.0) if order else 0.0
            )

    @api.depends('customer_vetting_sale_id', 'origin')
    def _compute_customer_vetting_product_detail_receipt(self):
        for picking in self:
            picking.customer_vetting_product_detail_receipt = (
                picking._customer_vetting_is_product_detail_so_receipt()
            )

    def _customer_vetting_is_product_detail_so_receipt(self):
        """True for incoming transfers created from the sales order product-detail vetting flow."""
        self.ensure_one()
        if self.customer_vetting_sale_id:
            return True
        origin = (self.origin or '').strip()
        return bool(origin.endswith(' | Product detail'))

    def _customer_vetting_product_detail_receipt_sale_order(self):
        """Resolve the sales order for a product-detail receipt (FK or legacy origin)."""
        self.ensure_one()
        if self.customer_vetting_sale_id:
            return self.customer_vetting_sale_id
        origin = (self.origin or '').strip()
        marker = ' | Product detail'
        if not origin.endswith(marker):
            return self.env['sale.order']
        name = origin[: -len(marker)]
        return self.env['sale.order'].search(
            [
                ('name', '=', name),
                ('company_id', '=', self.company_id.id),
            ],
            limit=1,
        )
