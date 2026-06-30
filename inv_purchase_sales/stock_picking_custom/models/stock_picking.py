from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    store_request_id = fields.Many2one('store.request', string='Store Request')
    approved_by = fields.Many2one(
        'res.users', string='Approved By', tracking=True, readonly=True)
    driver_name = fields.Char(string='Driver')
    driver_phone = fields.Char(string='Phone No')
    vehicle_plate = fields.Char(string='Truck / Plate No.')
    reason_for_entry = fields.Text(string='Reason')

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking in pickings:
            if not picking.sale_id:
                continue
            vals = {}
            if not picking.driver_name and picking.sale_id.driver_name:
                vals['driver_name'] = picking.sale_id.driver_name
            if not picking.driver_phone and picking.sale_id.driver_phone:
                vals['driver_phone'] = picking.sale_id.driver_phone
            if vals:
                picking.write(vals)
        return pickings

    def _grn_moves(self):
        self.ensure_one()
        return self.move_ids_without_package.filtered(lambda m: m.state != 'cancel')

    def get_grn_line_total(self, move):
        if move.line_subtotal:
            return move.line_subtotal
        qty = move.quantity or 0.0
        price = move.line_unit_price or 0.0
        if not price and move.purchase_line_id:
            price = move.purchase_line_id.price_unit
        return qty * price

    def get_grn_subtotal(self):
        self.ensure_one()
        return sum(self.get_grn_line_total(m) for m in self._grn_moves())

    def get_grn_grand_total(self):
        self.ensure_one()
        if self.purchase_id:
            return self.purchase_id.amount_total
        return self.get_grn_subtotal()

    def get_grn_move_gross_weight(self, move):
        return (
            getattr(move, 'grn_gross_weight', 0.0)
            or getattr(move, 'customer_vetting_gross_weight', 0.0)
            or 0.0
        )

    def get_grn_move_tare_weight(self, move):
        return (
            getattr(move, 'grn_tare_weight', 0.0)
            or getattr(move, 'customer_vetting_tare_weight', 0.0)
            or 0.0
        )

    def get_grn_move_net_weight(self, move):
        net = getattr(move, 'grn_net_weight', 0.0) or getattr(move, 'customer_vetting_line_net_weight', 0.0)
        if net:
            return net
        gross = self.get_grn_move_gross_weight(move)
        tare = getattr(move, 'grn_tare_weight', 0.0) or getattr(move, 'customer_vetting_tare_weight', 0.0)
        return gross - tare if gross or tare else (move.quantity or 0.0)

    def get_grn_so_po_ref(self):
        self.ensure_one()
        if self.purchase_id:
            return self.purchase_id.name
        if self.sale_id:
            return self.sale_id.name
        return self.origin or ''

    def get_cdn_invoice_ref(self):
        self.ensure_one()
        if self.sale_id:
            invoices = self.sale_id.invoice_ids.filtered(
                lambda m: m.move_type == 'out_invoice' and m.state == 'posted'
            )
            if invoices:
                return invoices[0].name
            return self.sale_id.name
        return self.origin or ''

    def get_gpa_customer(self):
        self.ensure_one()
        if self.partner_id:
            return self.partner_id
        if self.store_request_id and self.store_request_id.requested_by:
            return self.store_request_id.requested_by.partner_id
        return self.env['res.partner']

    def get_grn_amount_in_words(self):
        self.ensure_one()
        total = self.get_grn_grand_total()
        currency = self.company_id.currency_id
        if not currency or not total:
            return ''
        return currency.amount_to_text(total)

    def get_grn_cleaning_quality(self):
        self.ensure_one()
        for move in self._grn_moves():
            if getattr(move, 'grn_quality_pct', 0.0):
                return move.grn_quality_pct
        return 0.0

    def is_store_return_picking(self):
        self.ensure_one()
        picking_type = self.picking_type_id
        return (
            (picking_type.code == 'incoming' and picking_type.name == 'Delivery Return')
            or (picking_type.code == 'outgoing' and picking_type.name == 'Receipt Return')
        )

    def get_sra_source_doc_ref(self):
        self.ensure_one()
        return self.origin or ''

    def get_sra_returned_by(self):
        self.ensure_one()
        if self.store_request_id and self.store_request_id.requested_by:
            return self.store_request_id.requested_by
        if self.picking_type_id.code == 'incoming' and self.partner_id.user_id:
            return self.partner_id.user_id
        warehouse = self.location_id.warehouse_id
        if warehouse and warehouse.storeman_id:
            return warehouse.storeman_id
        return self.create_uid

    def get_sra_returned_by_name(self):
        self.ensure_one()
        user = self.get_sra_returned_by()
        if user:
            return user.name
        return self.partner_id.display_name or ''

    def get_sra_department_name(self):
        self.ensure_one()
        if self.store_request_id and self.store_request_id.department_id:
            return self.store_request_id.department_id.name
        return ''

    def get_sra_justification(self):
        self.ensure_one()
        return self.reason_for_entry or self.note or ''

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
