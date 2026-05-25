from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    store_request_id = fields.Many2one('store.request', string='Store Request')
    approved_by = fields.Many2one(
        'res.users', string='Approved By', tracking=True, readonly=True)
    carrier = fields.Many2one('res.users', string="Carrier")

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for rec in self:
            rec.approved_by = self.env.user.id
            # if rec.store_request_id and rec.picking_type_id.code == 'outgoing':
            #     employee = self.env['hr.employee'].search([
            #         ('user_id', '=', rec.store_request_id.requested_by.id)
            #     ])

            #     if not employee:
            #         raise UserError("no employee record for this user")

            #     for line in rec.move_ids_without_package:
            #         equipment = self.env['maintenance.equipment'].create({
            #             'name': line.product_id.name,
            #             'quantity': line.product_qty,
            #             'equipment_assign_to': 'employee',
            #             'assign_date': fields.Date.today(),
            #             'employee_id': employee.id,
            #             'cost': line.price_unit,
            #             'note': 'Created from Store Request: %s' % rec.name
            #         })
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    line_unit_price = fields.Float(
        string='Unit Price',
        compute='_compute_line_unit_price_subtotal',
        store=True,
        readonly=True,
        digits='Product Price',
    )
    line_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_line_unit_price_subtotal',
        store=True,
        readonly=True,
        currency_field='company_currency_id',
    )
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        depends=['company_id'],
    )

    def _linked_to_purchase(self):
        self.ensure_one()
        return bool(self.purchase_line_id) or bool(self.picking_id.purchase_id)

    def _linked_to_sale(self):
        self.ensure_one()
        return bool(self.sale_line_id) or bool(self.picking_id.sale_id)

    def _get_purchase_unit_price(self):
        self.ensure_one()
        if self.purchase_line_id:
            line = self.purchase_line_id
            if hasattr(line, '_get_gross_price_unit'):
                return line._get_gross_price_unit()
            return line.price_unit
        if self.picking_id.purchase_id and self.product_id:
            po_lines = self.picking_id.purchase_id.order_line.filtered(
                lambda l: l.product_id == self.product_id and not l.display_type
            )
            if po_lines:
                line = po_lines[0]
                if hasattr(line, '_get_gross_price_unit'):
                    return line._get_gross_price_unit()
                return line.price_unit
        return None

    def _get_sale_unit_price(self):
        self.ensure_one()
        if self.sale_line_id:
            return self.sale_line_id.price_unit
        if self.picking_id.sale_id and self.product_id:
            so_lines = self.picking_id.sale_id.order_line.filtered(
                lambda l: l.product_id == self.product_id and not l.display_type
            )
            if so_lines:
                return so_lines[0].price_unit
        return None

    def _get_product_unit_price(self):
        self.ensure_one()
        if not self.product_id:
            return 0.0
        return self.product_id.standard_price

    @api.depends(
        'product_id', 'product_id.standard_price',
        'purchase_line_id', 'purchase_line_id.price_unit',
        'sale_line_id', 'sale_line_id.price_unit',
        'picking_id', 'picking_id.purchase_id',
        'picking_id.purchase_id.order_line.price_unit',
        'picking_id', 'picking_id.sale_id',
        'picking_id.sale_id.order_line.price_unit',
        'quantity', 'product_uom_qty',
    )
    def _compute_line_unit_price_subtotal(self):
        for move in self:
            if move._linked_to_purchase():
                price = move._get_purchase_unit_price()
                if price is None:
                    price = move._get_product_unit_price()
            elif move._linked_to_sale():
                price = move._get_sale_unit_price()
                if price is None:
                    price = move._get_product_unit_price()
            else:
                price = move._get_product_unit_price()
            qty = move.quantity or move.product_uom_qty or 0.0
            move.line_unit_price = price
            move.line_subtotal = price * qty

    @api.constrains('quantity')
    def _check_quantity(self):
        for move in self:
            if move.quantity < 0:
                raise ValidationError("Quantity cannot be negative.")
