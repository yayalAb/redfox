from odoo import models, fields

# 1. ACTIVITY MASTER
class CorporateActivityMaster(models.Model):
    _name = 'corporate.activity.master'
    _description = 'Standardized Activity Library'

    name = fields.Char(string='Activity Name', required=True)
    department_id = fields.Many2one('hr.department', string='Department')
    uom_id = fields.Many2one('uom.uom', string='Default UOM')

# 2. FINANCIAL BUDGET HEADS
class CorporateFinancialItem(models.Model):
    _name = 'corporate.financial.item'
    _description = 'Budget Line Item Library'

    name = fields.Char(string='Item Name', required=True)
    category = fields.Selection([
        ('revenue', 'Revenue'),
        ('cos', 'Cost of Sales'),
        ('opex', 'Operating Expenses'),
        ('other', 'Other')
    ], string='Category', required=True)
    department_id = fields.Many2one('hr.department', string='Department')

# 3. CAPEX MASTER
class CorporateCapexItem(models.Model):
    _name = 'corporate.capex.item'
    _description = 'Standardized Asset/Capex Library'

    name = fields.Char(string='Asset/Project Name', required=True)
    department_id = fields.Many2one('hr.department', string='Department')


class CorporateStrategyType(models.Model):
    _name = 'corporate.strategy.type'
    _description = 'Business Strategy Type'

    name = fields.Char(string='Strategy Name', required=True, help="e.g. Cost Leadership, Differentiation")
    description = fields.Text(string='Description')
