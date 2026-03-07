from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    # Inherit the existing purchase.order model to add our new fields
    _inherit = 'purchase.order'


    # 2. The new "Payment Term" field for foreign orders
    x_payment_term_foreign = fields.Selection(
        selection=[
            ('lc', 'LC'),
            ('tt', 'TT'),
            ('cad', 'CAD'),
        ],
        string='Payment Method',
        tracking=True
    )
    x_port_of_loading = fields.Char(string="Port of Loading", tracking=True)
    x_terms_of_delivery = fields.Char(string="Terms of Delivery", tracking=True)
    x_bank_name = fields.Char(string="Bank Name", tracking=True)
    x_bank_account_number = fields.Char(string="Bank Account Number", tracking=True)
    x_swift_code = fields.Char(string="SWIFT Code", tracking=True)
    
     # THE FIX: Add a server-side constraint
    @api.constrains('purchase_origin', 'order_line', 'state')
    def _check_hs_code_for_foreign_purchase(self):
        """
        Server-side validation to ensure HS Codes are present for confirmed
        foreign purchase orders.
        """
        for order in self:
            if order.purchase_origin == 'foreign':
                # THE FIX: Loop through each line to find the first offender
                for line in order.order_line:
                    # We only care about lines with a product that is not a service/note
                    if line.product_id and line.display_type == False:
                        if not line.x_hs_code:
                            # Raise a specific error for THIS product, and then stop.
                            raise ValidationError(_(
                                "Product '%s' has no HS Code. Please set it on the product form before confirming.",
                                line.product_id.display_name
                            ))
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # This related field pulls the HS Code from the selected product.
    # Setting readonly=False means if a user types a code here,
    # it will be saved back to the product form automatically.
    x_hs_code = fields.Char(
        related='product_id.x_hs_code',
        string='HS Code',
        readonly=True,
        store=True, # Important for reporting and searching
    )