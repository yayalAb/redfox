from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    spare_parts = fields.One2many('maintenance.request.item', 'maintenance_request')
    store_request_ids = fields.One2many(
        'store.request', 
        'maintenance_request_id', 
        string='Store Requests'
    )
    breakdown_description = fields.Text(
        string='Breakdown Description'
    )

    root_cause = fields.Text(
        string='Root Cause'
    )
    store_request_count = fields.Integer(
        compute='_compute_store_request_count',
        string='Store Request Count'
    )

    @api.constrains('stage_id')
    def _check_stage_is_done(self):
        for record in self.filtered(lambda r: r.stage_id.done):

            pending_states = ['draft', 'submitted', 'store_review', 'approved']
        
            unissued_request_exists = self.env['store.request'].search_count([
                ('maintenance_request_id', '=', record.id),
                ('state', 'in', pending_states)
            ])

            if unissued_request_exists:
                raise UserError(_(
                    "You cannot complete this maintenance request ('%s') because it has "
                    "store requests that are not yet issued or cancelled."
                ) % record.name)


    @api.depends('store_request_ids')
    def _compute_store_request_count(self):
        for request in self:
            request.store_request_count = len(request.store_request_ids)

    def action_create_store_request(self):
        self.ensure_one()

        if self.stage_id.done:
            raise UserError(_("You cannot create a store request for a maintenance request that is already in a 'Done' stage (e.g., Repaired, Scrapped)."))

        if not self.spare_parts:
            raise UserError(_("Please add at least one spare part item before creating a store request."))

        # Prepare the lines for the new store request
        request_lines = []
        for line in self.spare_parts:
            request_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_uom.id,
                'remark': line.remark,
            }))

        # Create the store request
        store_request_vals = {
            'requested_by': self.env.user.id,
            'purpose': f"Spare parts for Maintenance Request {self.name}",
            'maintenance_request_id': self.id,
            'request_line_ids': request_lines,
        }
        
        store_request = self.env['store.request'].create(store_request_vals)



    def action_open_store_request(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Store Requests'),
            'res_model': 'store.request',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.store_request_ids.ids)],
            'context': {'default_maintenance_request_id': self.id}
        }
        # If there's only one request, open its form view directly
        if self.store_request_count == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.store_request_ids.id,
            })
        return action
    
class MaintenanceRequestItem(models.Model):
    _name = 'maintenance.request.item'

    maintenance_request = fields.Many2one('maintenance.request', string='Maintenance Request', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True)
    product_uom = fields.Many2one(related='product_id.uom_id', string='Unit of Meausure')
    remark = fields.Text(string='Remark') 