from odoo import fields, models


class InventoryBalanceReport(models.TransientModel):
    """A class for the transient model property.sale.report"""
    _name = 'inventory.balance.report'
    warehouse_ids = fields.Many2many('stock.warehouse',  string="Stores")
    stock_location_ids = fields.Many2many('stock.location', string="Location")

    tag_ids = fields.Many2many('product.tag', string="Tags")
    category_ids = fields.Many2many(
        'product.category', string="Product Category")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def action_create_report(self, group_by_location=False):
        """The function executes query related to the datas given
        and returns a pdf report"""
        domain = [('on_hand', '=', True)]
        move_line_domain = []
        warehouse_names = False
        if self.stock_location_ids:
            warehouse_names = self.stock_location_ids.mapped('name')
            domain.append(('location_id', 'in', self.stock_location_ids.ids))
            move_line_domain.append('|')
            move_line_domain.append(
                ('location_id', 'in', self.stock_location_ids.ids))
            move_line_domain.append(
                ('location_dest_id', 'in', self.stock_location_ids.ids))
        tags = False
        if self.tag_ids:
            tags = self.tag_ids.mapped('name')
            domain.append(
                ('product_id.product_tmpl_id.product_tag_ids', 'in', self.category_ids.ids))
        categories = False
        if self.category_ids:
            categories = self.category_ids.mapped('name')
            domain.append(('product_id.product_tmpl_id.categ_id',
                          'in', self.category_ids.ids))
        if self.start_date:
            move_line_domain.append(('date', '>=', self.start_date))
        if self.end_date:
            move_line_domain.append(('date', '<=', self.end_date))

        if group_by_location:
            group_by = ['product_id', 'location_id']
            cols = ['product_id', 'quantity:sum', 'location_id']
        else:
            cols = ['product_id', 'quantity:sum']
            group_by = ['product_id']
        stock_quant_grouped = self.env['stock.quant'].read_group(
            domain=domain,
            fields=cols,
            groupby=group_by,
            lazy=False
        )
        report_line_vals = []
        move_line_domain.append(('state', '=', 'done'))
        for record in stock_quant_grouped:
            product = self.env['product.product'].browse(
                record['product_id'][0])
            total_quantity = record['quantity']

            location = False
            if group_by_location:
                location = record['location_id'][0]
                product_domain = move_line_domain + \
                    [('product_id', '=', product.id), '|', ('location_id',
                                                            '=', location), ('location_dest_id', '=', location)]
            else:
                product_domain = move_line_domain + \
                    [('product_id', '=', product.id)]
            StockMove = self.env['stock.move.line'].search(product_domain)
            in_qyt = sum(StockMove.filtered(
                lambda m: m.location_usage not in ['internal', 'transit'] and m.location_dest_usage in ['internal',
                                                                                                        'transit']
            ).mapped('quantity'))
            out_qyt = sum(StockMove.filtered(
                lambda m: m.location_usage in ['internal', 'transit'] and m.location_dest_usage not in ['internal',
                                                                                                        'transit']
            ).mapped('quantity'))
            report_line_vals.append({
                'product_id': product.id,
                'default_code': product.default_code,
                'product_name': product.name,
                'stock_location_id': location,
                'incoming_qty': in_qyt,
                'outgoing_qty': out_qyt,
                'stock_balance': total_quantity,
                'unit_price': product.standard_price,
                'total_cost': product.standard_price * total_quantity,
            })
        data = {
            'datas': report_line_vals,
            'warehouses': warehouse_names,
            'tags': tags,
            'categories': categories,
        }
        return data

    def action_print(self):
        data = self.action_create_report()
        return self.env.ref(
            'inventory_report.inventory_balance_report_action_report_custom').report_action(
            self, data=data)

    def action_view(self):
        # Delete all existing records
        self.env['stock.balance.report.tree'].search([]).unlink()
        data = self.action_create_report()
        report_line_vals = data['datas']
        self.env['stock.balance.report.tree'].create(report_line_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inventory Balance',
            'res_model': 'stock.balance.report.tree',
            'view_mode': 'list',
            'target': 'current',
        }

    def action_view_detail(self):
        # Delete all existing records
        self.env['stock.balance.report.tree'].search([]).unlink()
        data = self.action_create_report(group_by_location=True)
        report_line_vals = data['datas']
        self.env['stock.balance.report.tree'].create(report_line_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inventory Balance',
            'res_model': 'stock.balance.report.tree',
            'view_mode': 'pivot',
            'target': 'current',
        }
