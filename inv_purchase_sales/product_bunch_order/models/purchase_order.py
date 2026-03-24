from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    product_bunch_id = fields.Many2one(
        'product.bunch.order',
        string='Product Bunch'
    )
    bunch_quantity = fields.Float(
        string='Bunch Quantity',
        default=1.0
    )

    def _get_bunch_lines(self):
        self.ensure_one()
        return self.order_line.filtered(lambda l: l.is_bunch_line or l.bunch_line_id)

    @api.onchange('product_bunch_id')
    def _onchange_product_bunch_id(self):
        for order in self:
            manual_lines = order.order_line - order._get_bunch_lines()
            new_bunch_lines = self.env['purchase.order.line']
            multiplier = order.bunch_quantity or 1.0

            if order.product_bunch_id:
                for bunch_line in order.product_bunch_id.line_ids:
                    product = bunch_line.product_id
                    line_vals = {
                        'product_id': product.id,
                        'name': product.display_name or product.name,
                        'product_qty': bunch_line.quantity * multiplier,
                        'product_uom': product.uom_po_id.id or product.uom_id.id,
                        'date_planned': order.date_order or fields.Datetime.now(),
                        'price_unit': product.standard_price or 0.0,
                        'is_bunch_line': True,
                        'bunch_line_id': bunch_line.id,
                    }
                    new_bunch_lines += self.env['purchase.order.line'].new(line_vals)

            order.order_line = manual_lines + new_bunch_lines

    @api.onchange('bunch_quantity')
    def _onchange_bunch_quantity(self):
        for order in self:
            multiplier = order.bunch_quantity or 1.0
            for line in order._get_bunch_lines().filtered('bunch_line_id'):
                line.product_qty = line.bunch_line_id.quantity * multiplier


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_bunch_line = fields.Boolean(string='Bunch Line', default=False)
    bunch_line_id = fields.Many2one(
        'product.bunch.order.line',
        string='Bunch Source Line'
    )
