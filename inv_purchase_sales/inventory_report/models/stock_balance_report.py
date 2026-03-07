from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, RedirectWarning, UserError
from odoo.osv import expression

class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_cost_report = fields.Float('Cost', compute='_compute_product_cost_report',store=True)

    @api.depends('standard_price')
    def _compute_product_cost_report(self):
        for rec in self:
            rec.product_cost_report=rec.standard_price


class InventoryStockBalanceReport(models.TransientModel):
    _name = "stock.balance.report.tree"
    _description = "Inventory Stock Balance Report"

    product_id = fields.Many2one('product.product', string="Product")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    stock_quant= fields.Many2one('stock.quant', string="Stock quant")
    default_code = fields.Char(string="Item Code")
    product_name = fields.Char(string="Item Name")
    incoming_qty = fields.Float(string="Received")
    outgoing_qty = fields.Float(string="Issued")
    stock_balance = fields.Float(string="Stock Balance")
    unit_price = fields.Float(string="Unit Price")
    total_cost = fields.Float(string="Total Price")