from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    guarantee_ids = fields.One2many('purchase.guarante', 'purchase_order_id', string="Purchase Guarantees")
    guarantee_count = fields.Integer(string="Guarantee Count", compute="_compute_guarantee_count")

    lc_number = fields.Char(string='LC Number')
    lc_amount = fields.Monetary(string='LC Amount')

    @api.depends('guarantee_ids')
    def _compute_guarantee_count(self):
        for order in self:
            order.guarantee_count = len(order.guarantee_ids)

    def action_view_guarantees(self):
        self.ensure_one()
        return {
            'name': 'Purchase Guarantees',
            'view_mode': 'list,form',
            'res_model': 'purchase.guarante',
            'domain': [('id', 'in', self.guarantee_ids.ids)],
            'type': 'ir.actions.act_window',
        }
    
    def action_create_guarantee(self):
        self.ensure_one()

        return {
            'name': 'Create Purchase Guarantee',
            'view_mode': 'form',
            'res_model': 'purchase.guarante',
            'type': 'ir.actions.act_window',
            'context': {'default_purchase_order_id': self.id},
        }