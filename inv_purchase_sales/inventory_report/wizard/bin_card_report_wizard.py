from odoo import fields, models
from datetime import datetime


class InventoryBalanceReport(models.TransientModel):
    """A class for the transient model property.sale.report"""
    _name = 'bin.card.report'
    warehouse_ids = fields.Many2many(
        'stock.warehouse', required=True, string="Stores")
    product_ids = fields.Many2many(
        'product.template', required=True, string="Products")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")

    def action_return_data(self):
        w_house = ""
        product_id = ""
        date_from_str = self.date_from.strftime(
            '%Y-%m-%d') if self.date_from else f"{datetime.today().year}-01-01"
        date_to_str = self.date_to.strftime(
            '%Y-%m-%d') if self.date_to else f"{datetime.today().year}-12-30"
        warehouse_names = False
        if self.warehouse_ids:
            warehouse_names = self.warehouse_ids.mapped('name')
            w_house = ""
            if len(self.warehouse_ids) > 1:
                warehouse_ids = tuple(self.warehouse_ids.ids)
                w_house += """ in %s""" % (warehouse_ids,)
            else:
                w_house += """ = %s""" % self.warehouse_ids.id
        if self.product_ids:

            if len(self.product_ids) > 1:
                product_ids = tuple(self.product_ids.ids)
                product_id += """ in %s""" % (product_ids,)
            else:
                product_id += """ = %s""" % self.product_ids.id

        query = f""" WITH stock_balance AS (
                            SELECT 
                                move.product_id,
                                SUM(CASE 
                                    WHEN move.location_dest_id IN (SELECT id FROM stock_location WHERE warehouse_id {w_house}) 
                                    THEN move.product_qty 
                                    ELSE -move.product_qty 
                                END) AS initial_balance
                            FROM stock_move move
                            JOIN product_product pp ON move.product_id = pp.id
                            JOIN product_template pt ON pp.product_tmpl_id = pt.id
                            JOIN stock_location sl ON move.location_id = sl.id OR move.location_dest_id = sl.id
                            WHERE move.state = 'done'
                              AND move.date < '{date_from_str}' 
                              AND sl.warehouse_id {w_house} 
                              AND pt.id {product_id}  
                            GROUP BY move.product_id
                        )

                        SELECT 
                            pt.id AS product_id,
                            pt.name->>'en_US' AS product_name,
                            pt.default_code AS item_code,
                            COALESCE(sb.initial_balance, 0) AS initial_balance, 
                            JSON_AGG(
                                JSON_BUILD_OBJECT(
                                    'move_id', sml.id,
                                    'date', TO_CHAR(move.date, 'YYYY-MM-DD'),
                                    'warehouse', sw.name,
                                    'in', CASE 
                                             WHEN move.location_dest_id IN (SELECT id FROM stock_location WHERE warehouse_id {w_house}) 
                                             THEN move.product_qty 
                                             ELSE 0 
                                         END,
                                    'out', CASE 
                                              WHEN move.location_id IN (SELECT id FROM stock_location WHERE warehouse_id {w_house}) 
                                              THEN move.product_qty 
                                              ELSE 0 
                                          END
                                ) 
                                ORDER BY move.date
                            ) AS move_details
                        FROM stock_move move
                        JOIN product_product pp ON move.product_id = pp.id
                        JOIN product_template pt ON pp.product_tmpl_id = pt.id
                        JOIN stock_location sl ON move.location_id = sl.id OR move.location_dest_id = sl.id
                        JOIN stock_warehouse sw ON sl.warehouse_id = sw.id
                        LEFT JOIN stock_balance sb ON move.product_id = sb.product_id 
                        LEFT JOIN stock_move_line sml ON sml.move_id = move.id  
                        WHERE sl.warehouse_id {w_house} 
                          AND move.state = 'done' 
                          AND pt.id {product_id}
                          AND move.date BETWEEN '{date_from_str}' AND '{date_to_str}'
                        GROUP BY pt.id, pt.name, pt.default_code, sb.initial_balance
                        ORDER BY pt.id; """
        self.env.cr.execute(query)
        datas = self.env.cr.dictfetchall()
        print(query)

        data = {
            'datas': datas,
            'warehouses': warehouse_names,
        }
        return data

    def action_print_pdf(self):
        data = self.action_return_data()
        return self.env.ref(
            'inventory_report.bin_card_report_action_report_custom').report_action(
            self, data=data)

    def action_view(self):
        datas = self.action_return_data()
        self.env['inventory.bin.card.report.tree'].search([]).unlink()
        report_line_vals = []
        for data in datas['datas']:
            qty_in = 0
            qnt_out = 0
            report_line_vals.append({
                'product_id': data['product_id'],
                'item_code': data['item_code'],
                'item_name': data['product_name'],
                'initial_balance': qty_in,
                'incoming_qty': 0,
                'outgoing_qty': 0,
                'stock_balance': qty_in,
            })
            for move in data['move_details']:
                qty_in += move['in']
                qnt_out += move['out']
                report_line_vals.append({
                    'move_id': move['move_id'],
                    'product_id': data['product_id'],
                    'item_code': data['item_code'],
                    'item_name': data['product_name'],
                    'date': move['date'],
                    'initial_balance': 0,
                    'incoming_qty': move['in'],
                    'outgoing_qty': move['out'],
                    'stock_balance': data['initial_balance'] + qty_in - qnt_out,
                })
            report_line_vals.append({
                'product_id': data['product_id'],
                'item_code': data['item_code'],
                'item_name': "Total",
                'initial_balance': data['initial_balance'],
                'incoming_qty': qty_in,
                'outgoing_qty': qnt_out,
                'stock_balance': data['initial_balance'] + qty_in - qnt_out,
            })

        self.env['inventory.bin.card.report.tree'].create(report_line_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bin Card Report',
            'res_model': 'inventory.bin.card.report.tree',
            'view_mode': 'list',
            'target': 'current',
            'context': {'search_default_group_by_item': 1},
        }
