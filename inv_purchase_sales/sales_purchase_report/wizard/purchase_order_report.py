from odoo import fields, models
from datetime import datetime


class PurchaseReport(models.TransientModel):
    """A class for the transient model property.sale.report"""
    _name = 'purchase.order.report'
    product_ids = fields.Many2many('product.template', string="Products")
    tag_ids = fields.Many2many('product.tag', string="Tags")
    category_ids = fields.Many2many(
        'product.category', string="Product Category")
    start_date = fields.Date(string="Date From")
    end_date = fields.Date(string="Date To")

    def action_return_data(self):
        product_id = ""
        category_id = ""
        tag_id = ""
        tags = False
        categories = False

        if self.product_ids:
            if len(self.product_ids) > 1:
                product_ids = tuple(self.product_ids.ids)
                product_id += """ and pt.id in %s""" % (product_ids,)
            else:
                product_id += """ and pt.id = %s""" % self.product_ids.id
        if self.category_ids:
            categories = self.category_ids.mapped('name')
            if len(self.category_ids) > 1:
                category_ids = tuple(self.category_ids.ids)
                category_id += """  and pt.categ_id in %s""" % (category_ids,)
            else:
                category_id += """ and pt.categ_id = %s""" % self.category_ids.id
        if self.tag_ids:
            tags = self.tag_ids.mapped('name')
            if len(self.tag_ids) > 1:
                tag_ids = tuple(self.tag_ids.ids)
                tag_id += """ WHERE product_tag_id in %s""" % (tag_ids,)
            else:
                tag_id += """ WHERE product_tag_id = %s""" % self.tag_ids.id
        date_range = ""
        if self.start_date and self.end_date:
            date_range = f" and sol.create_date <= '{self.end_date}' and sol.create_date >= '{self.start_date}' "
        elif self.start_date:
            date_range = f"and sol.create_date >= '{self.start_date}' "
        elif self.end_date:
            date_range = f" and sol.create_date <= '{self.end_date}'"

        query = f"""WITH unique_tags AS (
                   SELECT DISTINCT product_template_id FROM product_tag_product_template_rel 
				    {tag_id} ) 
				    SELECT
                    category_id,
                    category_name,
                    json_agg(
                        json_build_object(
                            'subcategory_id', subcategory_id,
                            'subcategory_name', subcategory_name,
                            'products', products
                        )
                    ) AS subcategories
                FROM (
                    SELECT
                        COALESCE(pc1.id, pc2.id) AS category_id,  -- If no parent, use own category
                        COALESCE(pc1.name, pc2.name) AS category_name,
                        CASE 
                            WHEN pc1.id IS NULL THEN NULL
                            ELSE pc2.id
                        END AS subcategory_id,
                        CASE 
                            WHEN pc1.id IS NULL THEN NULL
                            ELSE pc2.name
                        END AS subcategory_name,
                        json_agg(
                            json_build_object(
                                'product_id', product_id,
                                'product_name', product_name,
                                'default_code', default_code,
                                'total_quantity', total_quantity,
                                'total_sale_price', total_sale_price,
                                'total_price', total_price,
                                'price_tax', price_tax
                            )
                        ) AS products
                    FROM (
                        -- Product-level aggregation
                        SELECT
                            pt.id AS product_id,
                            pt.name->>'en_US' AS product_name,
                            pt.default_code AS default_code,
                            pt.categ_id AS category_id,
                            SUM(sol.product_uom_qty) AS total_quantity,
                            SUM(sol.price_unit * sol.product_uom_qty) AS total_sale_price,
                            SUM(sol.price_total) AS total_price,
                            SUM(sol.price_tax) AS price_tax
                        FROM purchase_order_line sol
                        JOIN sale_order so ON sol.order_id = so.id
                        JOIN product_product pp ON sol.product_id = pp.id
                        JOIN product_template pt ON pp.product_tmpl_id = pt.id
                        LEFT JOIN unique_tags ut ON pt.id = ut.product_template_id
                        WHERE so.state IN ('sale', 'done') {product_id} {category_id} {date_range}
                        GROUP BY pt.id, pt.name, pt.categ_id
                    ) AS product_data
                    LEFT JOIN product_category pc2 ON product_data.category_id = pc2.id
                    LEFT JOIN product_category pc1 ON pc2.parent_id = pc1.id
                    GROUP BY COALESCE(pc1.id, pc2.id), COALESCE(pc1.name, pc2.name),
                             CASE WHEN pc1.id IS NULL THEN NULL ELSE pc2.id END,
                             CASE WHEN pc1.id IS NULL THEN NULL ELSE pc2.name END
                ) AS subcategory_data
                GROUP BY category_id, category_name;"""
        self.env.cr.execute(query)
        datas = self.env.cr.dictfetchall()
        now = datetime.now()

        # Format it
        formatted_date = now.strftime("%A, %B %Y")
        data = {
            'datas': datas,
            'tags': tags,
            'categories': categories,
            'date': formatted_date,
        }
        return data

    def action_print_pdf(self):
        data = self.action_return_data()
        return self.env.ref(
            'sales_purchase_report.purchase_report_report_action_report_custom').report_action(
            self, data=data)

    def action_view(self):
        datas = self.action_return_data()
        self.env['purchase.report.tree'].search([]).unlink()
        datas = datas
        report_line_vals = []
        for data in datas['datas']:
            for sub_cat in data['subcategories']:
                report_line_vals.append({
                    'category_id': data['category_id'],
                    'sub_category_id': sub_cat['subcategory_id']
                })
                for product in sub_cat['products']:
                    report_line_vals.append({
                        'product_id': product['product_id'],
                        'quantity': product['total_quantity'],
                        'avg_amount': product['total_price']/product['total_quantity'],
                        'total_amount': product['total_price'],
                        'price_tax': product['price_tax']
                    })

        self.env['purchase.report.tree'].create(report_line_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Report',
            'res_model': 'sale.report.tree',
            'view_mode': 'list',
            'target': 'current',
        }
