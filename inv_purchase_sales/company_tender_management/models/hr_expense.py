from odoo import models, fields, api

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    sale_expense = fields.Boolean(string='Sale Expense', default=False, help='Indicates if this expense is related to a sale')