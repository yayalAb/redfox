from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StoreRequest(models.Model):
    _inherit = 'store.request'

    supplies_rfp_ids = fields.One2many(
        'supplies.rfp', 'store_request_id', string='Purchase Requests'
    )
    purchase_request_count = fields.Integer(
        compute='_compute_purchase_request_count', string='Purchase Request Count'
    )

    @api.depends('supplies_rfp_ids')
    def _compute_purchase_request_count(self):
        for rec in self:
            rec.purchase_request_count = len(rec.supplies_rfp_ids)

    def action_view_purchase_requests(self):
        self.ensure_one()
        return {
            'name': _('Purchase Requests'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'supplies.rfp',
            'domain': [('id', 'in', self.supplies_rfp_ids.ids)],
            'target': 'current',
        }

    def action_create_purchase_request(self):
        self.ensure_one()

        # Prepare the lines for the PO
        product_lines = []
        for line in self.request_line_ids:
            line_vals = {
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
            }
            product_lines.append((0, 0, line_vals))

        category_id = None
        if self.request_line_ids:
            category_id = self.request_line_ids[0].product_id.categ_id.id

        context = {
            'default_origin': self.name,
            'default_store_request_id': self.id,
            'default_product_line_ids': product_lines,
            'default_purpose': self.purpose,
            'default_state': 'draft',
            'default_project_id': self.project_id.id
        }

        if category_id:
            context['default_product_category_id'] = category_id

        return {
            'name': _('Purchase Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'supplies.rfp',
            'view_mode': 'form',
            'target': 'current',
            'context': context,
        }

    # Override the stock compute method if needed
    @api.depends('product_id', 'request_id.warehouse_id')
    def _compute_stock_available_qty_override(self):
        for line in self:
            if line.product_id and line.request_id.warehouse_id:
                variants = self.env['product.product'].search(
                    [('product_tmpl_id', '=', line.product_id.id)])
                if variants:
                    quants = self.env['stock.quant'].search([
                        ('product_id', 'in', variants.ids),
                        ('location_id', '=',
                         line.request_id.warehouse_id.lot_stock_id.id)
                    ])
                    line.stock_available_qty = sum(
                        quants.mapped('available_quantity'))
                else:
                    line.stock_available_qty = 0.0
            else:
                line.stock_available_qty = 0.0
