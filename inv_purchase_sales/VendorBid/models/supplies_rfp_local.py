from odoo import models, fields, api, _


class SuppliesRfpLocal(models.Model):
    _inherit = 'supplies.rfp'

    def _prepare_po_values(self, partner, lines_data):
        po_lines = []
        for line in lines_data:
            po_lines.append((0, 0, {
                'product_id': line['product'].id,
                'name': line['product'].name,
                'product_qty': line['qty'],
                'product_uom': line['uom'].id,
                'price_unit': line['price'],
            }))

        vals = {
            'rfp_id': self.id,
            'origin': self.rfp_number,
            'purchase_origin': self.purchase_origin,
            'company_id': self.company_id.id,
            'user_id': self.env.user.id,
            'order_line': po_lines,
            'state': 'sent',
        }

        if partner:
            vals['partner_id'] = partner.id
        if self.purchase_origin == 'foreign':
            vals.update({
                'currency_id': self.currency_id.id,
            })
        else:
            vals.update({
                'currency_id': self.env.company.currency_id.id,
            })

        return vals

    def action_open_po_creation_form(self):
        self.ensure_one()
        lines_data = []
        for line in self.product_line_ids:
            lines_data.append({
                'product': line.product_id,
                'qty': line.product_qty,
                'price': line.unit_price,
                'uom': line.product_uom,
                'description': line.description,
            })

        vals = self._prepare_po_values(partner=None, lines_data=lines_data)
        ctx = {f'default_{k}': v for k, v in vals.items()}
        return {
            'name': _('Create Purchase Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',
            'context': ctx,
        }
