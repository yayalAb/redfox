from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    accepted_order = fields.Boolean(string='Accepted', readonly=True)
    repeated_order = fields.Boolean(string='Repeated', readonly=False)


    def action_reorder(self):
        self.ensure_one()

        new_po = self.copy(default={
            'state': 'purchase',
            'repeated_order': True,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': new_po.id,
            'target': 'current',
        }

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    repeated_order = fields.Boolean(related='order_id.repeated_order', string='Repeated Order', store=True, readonly=True)