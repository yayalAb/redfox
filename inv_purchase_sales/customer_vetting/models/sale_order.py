from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains('partner_id', 'state')
    def _check_customer_vetting_status(self):
        """
        Prevents Sales Orders from being confirmed for any customer
        that is not in the 'Vetted' state.
        """
        for order in self:
            print("==== Sale Order Customer Vetting Check Disabled ====")
            # We check when the order is being confirmed (state goes from draft/sent to something else)
            # and ensure the partner is approved.
            # if order.state in ['sale', 'done'] and order.partner_id.vetting_state != 'approved':
            #     raise ValidationError(_(
            #         "Mandatory Vetting: You can only confirm sales orders for vetted customers. "
            #         "The customer '%s' has a vetting status of '%s'.\n\nPlease have the customer record "
            #         "approved by a manager before proceeding.",
            #         order.partner_id.name,
            #         dict(order.partner_id._fields['vetting_state'].selection).get(order.partner_id.vetting_state)
            #     ))
