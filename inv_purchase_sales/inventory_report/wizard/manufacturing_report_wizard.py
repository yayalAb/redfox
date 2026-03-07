from odoo import fields, models


class ManufacturingBalanceReport(models.TransientModel):
    """A class for the transient model property.sale.report"""
    _name = 'manufacturing.balance.report'
    warehouse_ids = fields.Many2many('stock.warehouse', string="Stores")
    tag_ids = fields.Many2many('product.tag', string="Tags")
    category_ids = fields.Many2many(
        'product.category', string="Product Category")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def action_create_report(self):
        """The function executes query related to the datas given
        and returns a pdf report"""
        warehouse_names = False
        warehouse = ""
        if self.warehouse_ids:
            warehouse_names = self.warehouse_ids.mapped('name')
            if len(self.warehouse_ids) > 1:
                warehouse_ids = tuple(self.warehouse_ids.ids)
                warehouse = """ AND sm.warehouse_id  IN %s""" % (
                    warehouse_ids,)
            else:
                warehouse = """ AND sm.warehouse_id  = %s """ % self.warehouse_ids.id

        tags = False
        tag = ""
        if self.tag_ids:
            tags = self.tag_ids.mapped('name')
            if len(self.tag_ids) > 1:
                tag_ids = tuple(self.tag_ids.ids)
                tag = """ WHERE product_tag_id IN %s """ % (tag_ids,)
            else:
                tag = """ WHERE product_tag_id = %s """ % self.tag_ids.id

        categories = False
        category = ""
        if self.category_ids:
            categories = self.category_ids.mapped('name')
            if len(self.category_ids) > 1:
                category_ids = tuple(self.category_ids.ids)
                category = """ AND pt.categ_id IN %s""" % (category_ids,)
            else:
                category = """ AND pt.categ_id = %s""" % self.category_ids.id
        date_range = ""
        if self.start_date and self.end_date:
            date_range = f" and date <= '{self.end_date}' and date >= '{self.start_date}' "
        elif self.start_date:
            date_range = f"and date >= '{self.start_date}' "
        elif self.end_date:
            date_range = f" and date <= '{self.end_date}'"

        query = f""" WITH unique_tags AS (
                   SELECT DISTINCT product_template_id FROM product_tag_product_template_rel 
				   {tag})
                   SELECT  pp.id AS product_id,
                        pp.default_code AS item_code,
                        pt.name->>'en_US' AS item_name,
                        COALESCE(SUM(CASE WHEN sm.location_dest_id IN
                            (SELECT id FROM stock_location WHERE usage = 'internal')
                            AND sm.location_id IN (SELECT id FROM stock_location WHERE usage = 'production')
                            THEN sm.product_qty END), 0) 
                            AS manufactured_amount,
                        COALESCE(SUM(CASE WHEN sm.location_id IN
                            (SELECT id FROM stock_location WHERE usage = 'internal')
                            AND sm.location_dest_id IN (SELECT id FROM stock_location WHERE usage = 'customer')
                            THEN sm.product_qty END), 0) 
                            AS delivered_amount,
                        pt.product_cost_report AS manufactured_cost
                    
                    FROM stock_move sm
                    JOIN product_product pp ON sm.product_id = pp.id
                    JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    JOIN product_category pc ON pt.categ_id = pc.id
                    LEFT JOIN unique_tags ut ON pt.id = ut.product_template_id
                    WHERE sm.state = 'done'
                         {warehouse}
                         {category}
                         {date_range}
                        GROUP BY pp.id, pp.default_code, pt.name, pt.product_cost_report
                        ORDER BY pp.id; """
        self.env.cr.execute(query)
        datas = self.env.cr.dictfetchall()
        data = {
            'datas': datas,
            'warehouses': warehouse_names,
            'tags': tags,
            'categories': categories,
        }

        return data

    def action_print(self):
        data = self.action_create_report()
        return self.env.ref(
            'inventory_report.manufacturing_document_report_custom').report_action(
            self, data=data)

    def action_view(self):
        # Delete all existing records
        self.env['manufactured.balance.report.tree'].search([]).unlink()
        data = self.action_create_report()
        report_line_vals = []
        for line in data['datas']:
            if line['manufactured_amount'] > 0:
                report_line_vals.append({
                    'product_id': line['product_id'],
                    'item_code': line['item_code'],
                    'item_name': line['item_name'],
                    'manufactured_amount': line['manufactured_amount'],
                    'delivered_amount': line['delivered_amount'],
                    'stock_balance': line['manufactured_amount'] - line['delivered_amount'],
                    'manufactured_cost': line['manufactured_cost'],
                    'total_manufactured_cost': (line['manufactured_amount'] - line['delivered_amount']) * line['manufactured_cost'],
                })

        self.env['manufactured.balance.report.tree'].create(report_line_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Balance',
            'res_model': 'manufactured.balance.report.tree',
            'view_mode': 'list',
            'target': 'current',
        }

    product_id = fields.Many2one('product.product', string="Product")
    item_code = fields.Char(string="Item Code")
    item_name = fields.Char(string="Item Name")
    manufactured_amount = fields.Float(string="Manufactured Amount")
    delivered_amount = fields.Float(string="Delivered Amount")
    stock_balance = fields.Float(string="Stock Balance")
    manufactured_cost = fields.Float(string="Manufactured Cost")
    total_manufactured_cost = fields.Float(string="Total Manufactured Cost")
