from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging


class AvailableWarehouseList(models.TransientModel):
    _name = 'avilable.warehouse.list'
    _description = 'product avilable warehouse list'

    store_request_id = fields.Many2one(
        'store.request',
        string='store Request',
        required=True,
        tracking=True
    )

    source_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Source Warehouse',
        required=True,
        tracking=True
    )

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Destnation Warehouse',
        required=True,
        tracking=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    product_uom_qty = fields.Float(
        string='Requested Quantity',
        required=True,
        default=1.0
    )
    product_uom = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True
    )
    product_category_id = fields.Many2one(
        related='product_id.categ_id',
        string='Category',
        store=True
    )
    stock_available_qty = fields.Float(
        string='Available Quantity',
        compute='_compute_stock_available_qty',
        store=True,
        digits='Product Unit of Measure'
    )

    request_qty = fields.Float(
        string='Requested Quantity',
    )

    @api.depends('product_id', 'source_warehouse_id')
    def _compute_stock_available_qty(self):
        for line in self:
            if line.product_id and line.source_warehouse_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.source_warehouse_id.lot_stock_id.id)
                ])
                line.stock_available_qty = sum(
                    quants.mapped('available_quantity'))
            else:
                line.stock_available_qty = 0.0

    def action_store_transfer(self):
        # self.ensure_one()
        for rec in self:
            transfer_request = self.env['store.transfer.request'].create({
                'store_request_id': rec.store_request_id.id,
                'requested_by': rec.env.user.id,
                'requested_date': fields.Datetime.today(),
                'source_warehouse_id': rec.source_warehouse_id.id,
                'warehouse_id': rec.warehouse_id.id,
                'request_line_ids': [(0, 0, {
                    'product_id': rec.product_id.id,
                    'product_uom_qty': rec.product_uom_qty,
                    'product_uom': rec.product_uom.id,
                })]})

            # Optionally return an action to open the created transfer request
            return {
                'name': _('Store Transfer Request'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'store.transfer.request',
                'res_id': transfer_request.id,
                'target': 'current',
            }


class StoreTransferRequestInherited(models.Model):
    _inherit = 'store.request'
    show_check_avilablity = fields.Boolean(
        compute="_check_avilablity", string="Check Avilablity")
    transfer_count = fields.Integer(
        string="Transfer Count", compute="_compute_transfer_count")

    def _compute_transfer_count(self):
        for rec in self:
            rec.transfer_count = self.env['store.transfer.request'].search_count([
                ('store_request_id', '=', rec.id)
            ])

    def action_store_request(self):
        return {
            'name': _('Stock Transfer'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'store.transfer.request',
            'target': 'current',
            'domain': [('store_request_id', '=', self.id)],

        }

    def _check_avilablity(self):
        for rec in self:
            warehouses = self.env['stock.warehouse'].search(
                [('id', '!=', self.warehouse_id.id)])
            check_other = False
            for stock_line in self.request_line_ids:
                if stock_line.product_uom_qty > stock_line.stock_available_qty:
                    check_other = True
                    break
            if len(warehouses) > 0 and check_other:
                rec.show_check_avilablity = True
            else:
                rec.show_check_avilablity = False

    def check_avilablity_on_other_stock(self):
        # self.ensure_one()
        # Get all warehouses except the requested one
        warehouses = self.env['stock.warehouse'].search([
            ('id', '!=', self.warehouse_id.id)
        ])

        # Create lines for each warehouse
        lines = []
        self.env['avilable.warehouse.list'].search([]).unlink()
        for wh in warehouses:
            for stock_line in self.request_line_ids:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', stock_line.product_id.id),
                    ('location_id', '=', wh.lot_stock_id.id)
                ])
                avilable_quantity = sum(
                    quants.mapped('available_quantity'))
                if avilable_quantity > 0:
                    self.env['avilable.warehouse.list'].create({
                        'store_request_id': self.id,
                        'source_warehouse_id': wh.id,
                        'warehouse_id': self.warehouse_id.id,
                        'product_id': stock_line.product_id.id,
                        'product_uom_qty': stock_line.product_uom_qty,
                        'product_uom': stock_line.product_uom.id
                    })

        return {
            'name': _('Stock Availability'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'avilable.warehouse.list',
            'target': 'new',
            'context': {
                'create': False,
                'edit': False,
            },
            'views': [(False, 'list')],
        }
