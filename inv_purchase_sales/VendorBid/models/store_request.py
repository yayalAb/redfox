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

    def action_create_purchase_request(self):
        self.ensure_one()

        product_lines = []

        for line in self.request_line_ids:
            qty_to_purchase = line.product_uom_qty - line.qty_issued

            if qty_to_purchase > 0:
                product_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': qty_to_purchase,
                    'product_uom': line.product_uom.id,
                    'description': line.description,
                }))

        if not product_lines:
            raise UserError(
                _("All requested items have already been fully issued from the store."))

        vals = {
            'store_request_id': self.id,
            'product_line_ids': product_lines,
            'purpose': self.note,
            'department_id': self.department_id.id,
            'state': 'draft',
        }

        if self.request_line_ids:
            vals['product_category_id'] = self.request_line_ids[0].product_id.categ_id.id
        rfp = self.env['supplies.rfp'].create(vals)

        return {
            'name': _('Purchase Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'supplies.rfp',
            'view_mode': 'form',
            'res_id': rfp.id,
            'target': 'current',
        }

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
    # # Override the stock compute method if needed
    # @api.depends('product_id', 'request_id.warehouse_id')
    # def _compute_stock_available_qty_override(self):
    #     for line in self:
    #         if line.product_id and line.request_id.warehouse_id:
    #             variants = self.env['product.product'].search(
    #                 [('product_tmpl_id', '=', line.product_id.id)])
    #             if variants:
    #                 quants = self.env['stock.quant'].search([
    #                     ('product_id', 'in', variants.ids),
    #                     ('location_id', '=',
    #                      line.request_id.warehouse_id.lot_stock_id.id)
    #                 ])
    #                 line.stock_available_qty = sum(
    #                     quants.mapped('available_quantity'))
    #             else:
    #                 line.stock_available_qty = 0.0
    #         else:
    #             line.stock_available_qty = 0.0
