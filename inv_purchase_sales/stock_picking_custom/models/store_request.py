from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StoreRequest(models.Model):
    _inherit = "store.request"

    picking_ids = fields.One2many(
        'stock.picking',
        'store_request_id',
        string='Transfer',
        readonly=True,
        copy=False,
    )
    issue_count = fields.Integer(compute='_compute_issue_count')
    issued_by = fields.Many2one(
        'res.users',
        string='Issued By',
        readonly=True,
        copy=False,
    )
    issued_date = fields.Date(string='Issued Date')

    @api.depends('picking_ids')
    def _compute_issue_count(self):
        for rec in self:
            rec.issue_count = len(rec.picking_ids)


    def action_store_issue(self):
        for rec in self:
            if not rec.warehouse_id:
                raise UserError(_("You must select a warehouse before issuing."))
            
            picking_type = rec.warehouse_id.int_type_id
            if not picking_type:
                raise UserError(_("No internal picking type found for the warehouse!"))

            location_dest_id = picking_type.default_location_dest_id.id

            if not location_dest_id:
                raise UserError(_("No destination location defined for the internal transfer."))
            
            move_lines = []
            
            for line in rec.request_line_ids:
                qty_remaining = line.product_uom_qty - line.qty_issued
                
                if qty_remaining <= 0:
                    continue

                line._compute_stock_available_qty()
                available_in_stock = line.stock_available_qty

                if available_in_stock <= 0:
                    continue

                qty_to_ship_now = min(qty_remaining, available_in_stock)

                if qty_to_ship_now > 0:
                    move_lines.append((0, 0, {
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': qty_to_ship_now,
                        'product_uom': line.product_uom.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': location_dest_id,
                    }))

                    line.write({
                        'qty_issued': line.qty_issued + qty_to_ship_now
                    })

                    if line.qty_issued >= line.product_uom_qty:
                        line.write({'line_state': 'issue'})
                    else:
                        line.write({'line_state': 'pending'})

            if not move_lines:
                raise UserError(_("No stock available for the remaining items."))

            self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': location_dest_id,
                'origin': rec.name,
                'store_request_id': rec.id,
                'move_ids_without_package': move_lines,
            })

            all_done = all(l.qty_issued >= l.product_uom_qty for l in rec.request_line_ids)
            if all_done:
                rec.write({'state': 'issue'})

        return True

    def action_open_pickings(self):
        self.ensure_one()
        return {
            'name': _('Transfers'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.picking_ids.ids)],
            'context': {'create': False},
        }