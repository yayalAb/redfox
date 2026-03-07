# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_request_ids = fields.One2many('payment.request', 'sale_order_id', string='Payment Requests')
    payment_request_count = fields.Integer(compute='_compute_pay_req_count')

    def _compute_pay_req_count(self):
        for order in self:
            order.payment_request_count = len(order.payment_request_ids)

    def action_create_payment_request(self):
        self.ensure_one()
        # 1. Validation
        if self.state not in ['sale', 'done']:
            raise ValidationError(_("You can only create a payment request for confirmed Sales Orders."))

        # 2. Prepare Product Lines
        req_lines = []
        for line in self.order_line:
            if not line.display_type:
                req_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'quantity': line.product_uom_qty,
                    'uom_id': line.product_uom.id,
                    'price_unit': line.price_unit,
                }))

        # 3. Prepare Header Data
        vals = {
            'sale_order_id': self.id,
            'partner_id': self.partner_id.id,
            'line_ids': req_lines,
            'subject': f"Payment Request for Order {self.name}",
            # Set default department if needed
            'department_name': 'Sourcing Contract Management', 
        }

        # 4. FIX: Check for Agreement and Pass it
        if hasattr(self, 'agreement_id') and self.agreement_id:
            vals['agreement_id'] = self.agreement_id.id
            
            # Generate the Reference Text manually because 'create' skips onchange methods
            ref_date = self.agreement_id.signature_date or fields.Date.today()
            ref_no = self.agreement_id.code or "N/A"
            vals['contract_ref_text'] = f"Ref: purchase orders No: {ref_no} Dated {ref_date}"

        # 5. Create the Record (This saves it to DB)
        request = self.env['payment.request'].create(vals)
        
        # 6. Open the Form View
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Request',
            'res_model': 'payment.request',
            'res_id': request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_payment_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Requests',
            'res_model': 'payment.request',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id}
        }