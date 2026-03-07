from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class StoreTransferRequest(models.Model):
    _name = 'store.transfer.request'
    _description = 'Store Transfer Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'requested_date desc'

    store_request_id = fields.Many2one(
        'store.request',
        string='store Request'
    )
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        default=lambda self: _('New'),
        readonly=True
    )
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    department_id = fields.Many2one(
        'hr.department',
        related='requested_by.employee_id.department_id',
        string='Department',
        required=True,
        tracking=True
    )
    requested_date = fields.Datetime(
        string='Requested Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    source_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Source Warehouse',
        tracking=True
    )

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Destnation Warehouse',
        required=True,
        tracking=True
    )
    request_line_ids = fields.One2many(
        'store.transfer.request.line',
        'request_id',
        string='Request Lines',
        required=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('transfered', 'Transfer Requested'),
        ('cancel', 'Cancelled')],
        string='State',
        default='draft',
        tracking=True
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        tracking=True
    )
    storeman_id = fields.Many2one(
        'res.users',
        related="source_warehouse_id.storeman_id",
        string='Storeman',
        tracking=True
    )
    note = fields.Html(string='Note')
    is_department_head = fields.Boolean(
        compute="_check_department_head", string="Is Department Head")
    is_storeman = fields.Boolean(
        compute="_check_is_storeman", string="Is Storeman")
    transfer_id = fields.Many2one(
        'stock.picking',
        string='Transfer',
        readonly=True,
        copy=False,
    )

    @api.depends("department_id")
    def _check_department_head(self):
        for rec in self:
            if rec.department_id.manager_id.id == self.env.user.employee_id.id:
                rec.is_department_head = True
            else:
                rec.is_department_head = False

    @api.depends("warehouse_id")
    def _check_is_storeman(self):
        for rec in self:
            if rec.storeman_id.id == self.env.user.id:
                rec.is_storeman = True
            else:
                rec.is_storeman = False

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'store.transfer.request') or _('New')
        res = super(StoreTransferRequest, self).create(vals)
        # if res.department_id.manager_id.id == res.requested_by.employee_id.id:
        #     res.state = 'approved'
        return res

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id
        })

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_store_transfer(self):
        for rec in self:
            # Validate that source warehouse is set
            if not rec.source_warehouse_id:
                raise UserError(
                    _("Source warehouse must be specified for internal transfer!"))

            # Use the internal transfer picking type of the destination warehouse
            picking_type = rec.warehouse_id.int_type_id or self.env['stock.picking.type'].search([
                ('code', '=', 'internal'),
                ('warehouse_id', '=', rec.warehouse_id.id)
            ], limit=1)

            if not picking_type:
                raise UserError(
                    _("No internal transfer picking type found for the destination warehouse!"))

            # Prepare move lines
            move_lines = []
            for line in rec.request_line_ids:
                # Check available quantity in source location
                available_qty = line.product_id.with_context(
                    location=rec.source_warehouse_id.lot_stock_id.id
                ).qty_available

                if available_qty < line.product_uom_qty:
                    raise UserError(_(
                        "Not enough quantity available for product %s in source warehouse! "
                        "Available: %s, Requested: %s") % (
                        line.product_id.name,
                        available_qty,
                        line.product_uom_qty
                    ))

                move_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'location_id': rec.source_warehouse_id.lot_stock_id.id,
                    'location_dest_id': rec.warehouse_id.lot_stock_id.id,
                }))

            # Create the picking
            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': rec.source_warehouse_id.lot_stock_id.id,
                'location_dest_id': rec.warehouse_id.lot_stock_id.id,
                'origin': rec.name,
                'move_ids_without_package': move_lines,
                'store_transfer_request_id': self.id,
            })

            rec.write({
                'state': 'transfered',
                'transfer_id': picking.id
            })

        return True

    def action_open_transfer(self):
        self.ensure_one()  # Ensures this method works on a single record
        if not self.transfer_id:
            raise UserError(_("No transfer is linked to this request!"))

        return {
            'name': _('Stock Transfer'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.transfer_id.id,
            'target': 'current',

        }


class StoreTransferRequestLine(models.Model):
    _name = 'store.transfer.request.line'
    _description = 'Store Request Line'

    request_id = fields.Many2one(
        'store.transfer.request',
        string='Request',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    product_uom_qty = fields.Float(
        string='Quantity',
        required=True,
        default=1.0
    )
    product_uom = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True
    )

    stock_available_qty = fields.Float(
        string='Available Quantity',
        compute='_compute_stock_available_qty',
        store=True,
        digits='Product Unit of Measure'
    )

    @api.depends('product_id', 'request_id.source_warehouse_id')
    def _compute_stock_available_qty(self):
        for line in self:
            if line.product_id and line.request_id.source_warehouse_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=',
                     line.request_id.source_warehouse_id.lot_stock_id.id)
                ])
                line.stock_available_qty = sum(
                    quants.mapped('available_quantity'))
            else:
                line.stock_available_qty = 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id
            return {'domain': {
                'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]
            }}

    @api.constrains('product_uom_qty')
    def _check_positive_qty(self):
        for line in self:
            if line.product_uom_qty <= 0:
                raise ValidationError(_('Quantity must be positive!'))

    @api.constrains('product_uom')
    def _check_uom_category(self):
        for line in self:
            if line.product_id and line.product_uom.category_id != line.product_id.uom_id.category_id:
                raise ValidationError(
                    _('The unit of measure must be in the same category as the product unit of measure'))
