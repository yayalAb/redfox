from collections import defaultdict

from odoo import models, fields, api
from odoo.exceptions import UserError

class SuppliesRfp(models.Model):
    _inherit = 'supplies.rfp'

    comparison_table = fields.Html(compute="_compute_comparison_table", string="Bid Comparison Table")

    def action_recommend_best_prices(self):
            self.ensure_one()
            self.rfq_line_ids.write({'recommended': False})

            valid_lines = self.rfq_line_ids.filtered(lambda l: l.price_unit > 0)
            if not valid_lines:
                raise UserError("There are no RFQ lines with a valid unit price (greater than zero) to recommend.")
            
            lines_by_product = defaultdict(lambda: self.env['purchase.order.line'])
            for line in valid_lines:
                lines_by_product[line.product_id] |= line

            if not lines_by_product:
                raise UserError("There are no RFQ lines to recommend.")

            # Find the best price for each product
            recommended_lines = self.env['purchase.order.line']
            for product, lines in lines_by_product.items():
                # Find the line with the minimum price_unit
                best_line = min(lines, key=lambda l: l.price_subtotal)
                recommended_lines |= best_line
            
            # Mark the best lines as recommended
            if recommended_lines:
                recommended_lines.write({'recommended': True})


    def action_create_bid_purchase_orders(self):

            self.ensure_one()
            recommended_lines = self.rfq_line_ids.filtered(lambda l: l.recommended)
            
            if not recommended_lines:
                raise UserError("There are no recommended lines to create Purchase Orders from. Please run the 'Recommend Best Prices' action first.")

            # Group recommended lines by supplier (partner_id on the purchase.order)
            lines_by_supplier = defaultdict(lambda: self.env['purchase.order.line'])
            for line in recommended_lines:
                lines_by_supplier[line.order_id.partner_id] |= line

            created_pos = self.env['purchase.order']
            for supplier, lines in lines_by_supplier.items():
                po_vals = {
                    'partner_id': supplier.id,
                    'rfp_id': self.id,
                    'origin': self.rfp_number,
                    'order_line': [],
                    'currency_id': self.currency_id.id,
                    'purchase_origin': self.purchase_origin,
                    'final_po': True,
                    'state': 'to approve',
                }
                for line in lines:
                    line_vals = {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.price_unit,
                    }
                    po_vals['order_line'].append((0, 0, line_vals))
                
                new_po = self.env['purchase.order'].create(po_vals)
                created_pos |= new_po

            self.write({'state': 'ordered', 'date_ordered':  fields.Date.today()})


    def _compute_comparison_table(self):
        for rec in self:
            valid_rfq_lines = rec.rfq_line_ids.filtered(
                lambda l: l.order_id.final_po == False
            )

            vendors = valid_rfq_lines.mapped('partner_id')
            products = rec.product_line_ids.mapped('product_id')

            if not vendors or not products:
                rec.comparison_table = "<p>No RFQs or Products found to compare.</p>"
                continue

            # 2. Build the Table Header
            table_html = """
                <table class="table table-sm table-bordered o_main_table">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th class="text-left">Product / Description</th>
                            <th class="text-center">Qty</th>
            """
            # Add a column for each Vendor
            for vendor in vendors:
                table_html += f'<th class="text-center" style="min-width: 120px;">{vendor.name}</th>'
            
            table_html += "</tr></thead><tbody>"

            # 3. Build Table Rows (One row per product)
            for product_line in rec.product_line_ids:
                prod = product_line.product_id
                table_html += f"""
                    <tr>
                        <td><strong>{prod.display_name}</strong><br/><small>{product_line.description or ''}</small></td>
                        <td class="text-center">{product_line.product_qty} {product_line.product_uom.name}</td>
                """

                # 4. Fill Price for each Vendor Column
                for vendor in vendors:
                    # Look for the price from this specific vendor for this specific product
                    line = rec.rfq_line_ids.filtered(lambda l: l.product_id == prod and l.partner_id == vendor)
                    
                    if line:
                        # Logic to highlight if recommended
                        bg_style = "background-color: #d4edda;" if line[0].recommended else ""
                        price = f"{line[0].price_unit:,.2f}"
                        table_html += f'<td class="text-center" style="{bg_style}">{price}</td>'
                    else:
                        table_html += '<td class="text-center text-muted">-</td>'

                table_html += "</tr>"

            table_html += "</tbody></table>"
            rec.comparison_table = table_html