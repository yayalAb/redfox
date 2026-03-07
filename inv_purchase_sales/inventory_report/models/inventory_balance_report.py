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
    stock_location_id = fields.Many2one('stock.location', string="Location")
    default_code = fields.Char(string="Item Code")
    product_name = fields.Char(string="Item Name")
    incoming_qty = fields.Float(string="Received")
    outgoing_qty = fields.Float(string="Issued")
    stock_balance = fields.Float(string="Stock Balance")
    unit_price = fields.Float(string="Unit Price")
    total_cost = fields.Float(string="Total Price")






class ManufacturingStockBalanceReport(models.TransientModel):
    _name = "manufactured.balance.report.tree"
    _description = "Manufactured Stock Balance Report"

    product_id = fields.Many2one('product.product', string="Product")
    item_code = fields.Char(string="Item Code")
    item_name = fields.Char(string="Item Name")
    manufactured_amount = fields.Float(string="Manufactured Amount")
    delivered_amount = fields.Float(string="Delivered Amount")
    stock_balance = fields.Float(string="Stock Balance")
    manufactured_cost = fields.Float(string="Manufactured Cost")
    total_manufactured_cost = fields.Float(string="Total Manufactured Cost")

class InventoryBinCardReport(models.TransientModel):
    _name = "inventory.bin.card.report.tree"
    _description = "Inventory bin card report"

    product_id = fields.Many2one('product.template', string="Product")
    move_id = fields.Many2one('stock.move.line', string="Origin")
    item_code = fields.Char(string="Item Code")
    item_name = fields.Char(string="Item Name")
    date = fields.Date(string="Date")
    initial_balance = fields.Float(string="Initial Balance")
    incoming_qty = fields.Float(string="Received")
    outgoing_qty = fields.Float(string="Issued")
    stock_balance = fields.Float(string="Stock Balance")


