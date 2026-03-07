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

    @api.constrains('quantity')
    def _check_quantity(self):
        for move in self:
            if move.quantity < 0:
                raise ValidationError("Quantity cannot be negative.")
