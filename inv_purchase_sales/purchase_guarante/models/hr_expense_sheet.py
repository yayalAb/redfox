from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    guarantee_id = fields.Many2one('purchase.guarante', string='Purchase Guarantee')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    foreign_purchase = fields.Boolean(string='Foreign Purchase Payments', default=False)
    declaration_number = fields.Char(string='Declaration Number')
    lc_number = fields.Char(string='LC Number')
    account_type = fields.Char(string='Account Type')
    account_number = fields.Char(string='Account Number')
    foreign_currency_id = fields.Many2one('res.currency', string="Foreign Currency", default=lambda self: self.env.company.currency_id)
    foreign_currency_amount = fields.Monetary(string='Foreign Currency Amount', currency_field='currency_id')
    payment_type = fields.Selection([
        ('cpo', 'CPO'),
        ('transfer', 'Transfer'),
        ('cheque', 'Cheque')
    ], string='Payment Type', default='cpo')


    def action_print_payment_request(self):
        self.ensure_one()
        if self.foreign_purchase:
            return self.env.ref('purchase_guarante.action_report_foreign_purchase_payment_request').report_action(self)
        else:
            return self.env.ref('payment_request.action_report_payment_request').report_action(self)