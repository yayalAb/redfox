# -*- coding: utf-8 -*-
from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    customer_vetting_sale_id = fields.Many2one(
        'sale.order',
        string='Sales order (product detail receipt)',
        ondelete='set null',
        copy=False,
        index=True,
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

    def _customer_vetting_create_grain_cleaning_from_receipt(self):
        """Create a draft grain cleaning process when the product-detail receipt is validated."""
        self.ensure_one()
        if self.state != 'done':
            return
        order = self._customer_vetting_product_detail_receipt_sale_order()
        if not order:
            return
        order_sudo = order.sudo()
        if order_sudo.grain_cleaning_process_id:
            return

        Process = self.env['grain.cleaning.process']
        line_cmds = []
        for sol in order_sudo.order_line.filtered(
            lambda l: not l.display_type and l.product_id and l.product_id.type == 'service'
        ):
            p_uom = sol.product_id.uom_id
            req_uom = sol.product_uom
            uom = req_uom if req_uom and req_uom.category_id == p_uom.category_id else p_uom
            line_cmds.append(
                (
                    0,
                    0,
                    {
                        'product_id': sol.product_id.id,
                        'product_uom_qty': sol.product_uom_qty,
                        'product_uom_id': uom.id,
                        'name': sol.name,
                    },
                )
            )

        process = Process.create(
            {
                'partner_id': order_sudo.partner_id.id,
                'company_id': order_sudo.company_id.id,
                'line_ids': line_cmds,
                'receipt_source_sale_order_id': order_sudo.id,
            }
        )
        order_sudo.write({'grain_cleaning_process_id': process.id})
        process.message_post(
            body=_('Created when product detail receipt %s was validated.')
            % (self.display_name,)
        )
        order_sudo.message_post(
            body=_('Grain cleaning %s was opened from receipt %s.')
            % (process._get_html_link(), self.display_name)
        )

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            if (
                picking.state == 'done'
                and picking._customer_vetting_is_product_detail_so_receipt()
            ):
                picking._customer_vetting_create_grain_cleaning_from_receipt()
        return res
