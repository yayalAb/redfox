from collections import defaultdict

from odoo import models, fields, api
from odoo.exceptions import UserError

class SuppliesRfp(models.Model):
    _inherit = 'supplies.rfp'

    comparison_table = fields.Html(compute="_compute_comparison_table", string="Bid Comparison Table")

    def action_recommend_best_prices(self):
            self.ensure_one()
            self.rfq_line_ids.write({'recommended': False})

            # Exclude lines with out_of_stock status and lines with price_unit <= 0
            valid_lines = self.rfq_line_ids.filtered(
                lambda l: l.price_unit > 0 and not l.out_of_stock
            )
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
                # Find the line with the minimum price_subtotal
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
                    'state': 'sent',  # Start in 'sent' state, will move to 'committee_approved' when all approve
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

    def create_order_from_winners(self):
        """
        Create purchase orders from winning vendors based on their winning quantities and prices.
        Winning lines are determined by the lowest price_subtotal for each product.
        """
        self.ensure_one()
        
        # Get valid RFQ lines (exclude out of stock and cancelled orders)
        valid_rfq_lines = self.rfq_line_ids.filtered(
            lambda l: l.order_id.final_po == False and l.order_id.state != 'cancel'
        )
        
        if not valid_rfq_lines:
            raise UserError("There are no valid RFQ lines to create purchase orders from.")
        
        # Find winning lines (lowest price_subtotal for each product)
        winning_lines_by_supplier = self.env['purchase.order.line']
        for product_line in self.product_line_ids:
            prod = product_line.product_id
            all_lines_for_product = valid_rfq_lines.filtered(
                lambda l: l.product_id == prod and not l.out_of_stock and l.price_subtotal > 0
            )
            if all_lines_for_product:
                winning_line = min(all_lines_for_product, key=lambda l: l.price_subtotal)
                winning_lines_by_supplier |= winning_line
        
        if not winning_lines_by_supplier:
            raise UserError("No winning lines found. Please ensure there are valid RFQ lines with prices.")
        
        # Group winning lines by supplier
        lines_by_supplier = defaultdict(lambda: self.env['purchase.order.line'])
        for line in winning_lines_by_supplier:
            lines_by_supplier[line.order_id.partner_id] |= line
        
        # Create purchase orders for each supplier
        created_pos = self.env['purchase.order']
        for supplier, lines in lines_by_supplier.items():
            po_vals = {
                'partner_id': supplier.id,
                'rfp_id': self.id,
                'store_request_id': self.store_request_id.id if self.store_request_id else False,
                'origin': self.rfp_number,
                'order_line': [],
                'currency_id': self.currency_id.id,
                'purchase_origin': self.purchase_origin,
                'final_po': True,
                'state': 'sent',  # Start in 'sent' state
            }
            
            # Copy taxes from the original RFQ order if available
            source_rfq = lines[0].order_id if lines else False
            if source_rfq:
                if hasattr(source_rfq, 'applied_tax_ids') and source_rfq.applied_tax_ids:
                    po_vals['applied_tax_ids'] = [(6, 0, source_rfq.applied_tax_ids.ids)]
                if hasattr(source_rfq, 'price_tax_included'):
                    po_vals['price_tax_included'] = source_rfq.price_tax_included
            
            # Add order lines with winning quantities and prices
            for line in lines:
                line_vals = {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_qty': line.product_qty,  # Winning quantity
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,  # Winning price
                }
                
                # Copy taxes from the winning line if available
                if line.taxes_id:
                    line_vals['taxes_id'] = [(6, 0, line.taxes_id.ids)]
                
                po_vals['order_line'].append((0, 0, line_vals))
            
            new_po = self.env['purchase.order'].create(po_vals)
            created_pos |= new_po
        
        # Update RFP state
        self.write({'state': 'ordered', 'date_ordered': fields.Date.today()})
        
        # Return action to show created purchase orders
        if len(created_pos) == 1:
            return {
                'name': 'Purchase Order',
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': created_pos.id,
                'target': 'current',
            }
        else:
            # For multiple orders, show list view
            return {
                'name': f'Purchase Orders ({len(created_pos)} created)',
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_pos.ids)],
                'target': 'current',
            }

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

            # Pre-calculate winning prices for each product (lowest price_subtotal)
            winning_prices = {}
            for product_line in rec.product_line_ids:
                prod = product_line.product_id
                all_lines_for_product = valid_rfq_lines.filtered(
                    lambda l: l.product_id == prod and not l.out_of_stock and l.price_subtotal > 0
                )
                if all_lines_for_product:
                    winning_line = min(all_lines_for_product, key=lambda l: l.price_subtotal)
                    winning_prices[prod.id] = winning_line.id

            # Get unique RFQs and sort by amount_total - include all RFQs (even out of spec/stock)
            rfqs = valid_rfq_lines.mapped('order_id')
            sorted_rfqs = rfqs.sorted(key=lambda r: r.amount_total if r.amount_total else 0)
            # Include all RFQs, even those with out of spec/stock status
            all_rfqs = [r for r in sorted_rfqs if r.partner_id in vendors]
            
            # Determine layout: products as rows if products > suppliers
            product_count = len(rec.product_line_ids)
            supplier_count = len(all_rfqs)
            use_products_as_rows = product_count > supplier_count

            # Build the Table Header
            table_html = """
                <div style="font-family: 'Noto Sans Ethiopic', 'Times New Roman', serif; font-size: 12px;">
                    <div class="text-center" style="font-weight: bold; margin-bottom: 5px; margin-top: 15px;">
                        Item Description and Suppliers List Table
                    </div>
            """
            
            # Layout 1: Products as Rows, Suppliers as Columns (when products > suppliers)
            if use_products_as_rows:
                table_html += """
                    <table style="width: 100%; border-collapse: collapse; border: 1px solid black; font-size: 10px;">
                        <thead style="background-color: #f0f0f0;">
                            <tr>
                                <th rowspan="2" style="border: 1px solid black; padding: 5px; text-align: center; width: 3%;">No.</th>
                                <th rowspan="2" style="border: 1px solid black; padding: 5px; text-align: center; width: 20%;">Product Description</th>
                                <th rowspan="2" style="border: 1px solid black; padding: 5px; text-align: center; width: 8%;">Qty (UOM)</th>
                """
                
                # Add supplier columns
                for rfq in all_rfqs:
                    table_html += f"""
                                <th colspan="2" style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span>{rfq.partner_id.name}</span>
                                </th>
                    """
                
                table_html += """
                            </tr>
                            <tr>
                """
                
                # Add Unit Price / Total headers for each supplier
                for rfq in all_rfqs:
                    table_html += """
                                <th style="border: 1px solid black; padding: 2px; text-align: center; border-right: 1px dotted gray;">Unit Price</th>
                                <th style="border: 1px solid black; padding: 2px; text-align: center;">Total</th>
                    """
                
                table_html += """
                            </tr>
                        </thead>
                        <tbody>
                """
                
                # Build product rows
                row_idx = 0
                for product_line in rec.product_line_ids:
                    prod = product_line.product_id
                    row_idx += 1
                    
                    table_html += f"""
                            <tr>
                                <td style="border: 1px solid black; padding: 2px; text-align: center; vertical-align: middle;">
                                    <span>{row_idx}</span>
                                </td>
                                <td style="border: 1px solid black; padding: 2px; vertical-align: middle;">
                                    <span>{prod.display_name}</span>
                    """
                    if product_line.description:
                        table_html += f"""
                                        <br />
                                        <span>{product_line.description}</span>
                        """
                    table_html += """
                                </td>
                                <td style="border: 1px solid black; padding: 2px; text-align: center; vertical-align: middle;">
                    """
                    table_html += f"""
                                    <span>{int(product_line.product_qty)}</span> (<span>{product_line.product_uom.name if product_line.product_uom else ''}</span>)
                                </td>
                    """
                    
                    # Fill supplier columns
                    for rfq in all_rfqs:
                        rfq_line = valid_rfq_lines.filtered(
                            lambda l: l.product_id == prod and l.order_id == rfq
                        )
                        
                        is_out_of_spec = rfq.amount_total == 0 or rfq.state == 'cancel'
                        stock_status = rfq_line and rfq_line[0].out_of_stock or False
                        is_winning_price = rfq_line and rfq_line[0].id == winning_prices.get(prod.id, False) if rfq_line else False
                        winning_bg_color = 'background-color: #cccccc;' if is_winning_price else ''
                        
                        if stock_status == 'out_of_stock' or stock_status == 'out_of_specification':
                            status_text = "Out of Stock" if stock_status == 'out_of_stock' else "Out of Specification"
                            table_html += f"""
                                <td colspan="2" style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">{status_text}</span>
                                </td>
                            """
                        elif is_out_of_spec:
                            table_html += """
                                <td colspan="2" style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">Out of Spec</span>
                                </td>
                            """
                        else:
                            if rfq_line:
                                unit_price = rfq_line[0].price_unit
                                total_price = rfq_line[0].price_subtotal
                                table_html += f"""
                                <td style="border: 1px solid black; border-right: 1px dotted gray; padding: 2px; text-align: right;">
                                    <span>{unit_price:,.2f}</span>
                                </td>
                                <td style="border: 1px solid black; padding: 2px; text-align: right; {winning_bg_color}">
                                    <span>{total_price:,.2f}</span>
                                </td>
                            """
                            else:
                                table_html += """
                                <td style="border: 1px solid black; border-right: 1px dotted gray; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">-</span>
                                </td>
                                <td style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">-</span>
                                </td>
                            """
                    
                    table_html += """
                            </tr>
                    """
                
                table_html += """
                        </tbody>
                    </table>
                """
            
            # Layout 2: Suppliers as Rows, Products as Columns (when suppliers >= products)
            else:
                table_html += """
                    <table style="width: 100%; border-collapse: collapse; border: 1px solid black; font-size: 10px;">
                        <thead style="background-color: #f0f0f0;">
                            <tr>
                                <th rowspan="3" style="border: 1px solid black; padding: 5px; text-align: center; width: 3%;">No.</th>
                                <th rowspan="3" style="border: 1px solid black; padding: 5px; text-align: center; width: 15%;">Suppliers List Table</th>
                """
                
                # Add product columns with colspan="2" for Unit Price and Total
                for product_line in rec.product_line_ids:
                    prod = product_line.product_id
                    table_html += f"""
                                <th colspan="2" style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span>{prod.display_name}</span>
                                    <br />
                                    <span>{product_line.description or ''}</span>
                                </th>
                    """
                
                table_html += """
                                <th rowspan="3" style="border: 1px solid black; padding: 5px; text-align: center; width: 8%;">Total</th>
                            </tr>
                            <tr>
                """
                
                # Add UOM row for each product
                for product_line in rec.product_line_ids:
                    table_html += f"""
                                <th colspan="2" style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span>{int(product_line.product_qty)}</span>(<span>{product_line.product_uom.name}</span>)
                                </th>
                    """
                
                table_html += """
                            </tr>
                            <tr>
                """
                
                # Add Unit Price and Total headers for each product
                for product_line in rec.product_line_ids:
                    table_html += """
                                <th style="border: 1px solid black; padding: 2px; text-align: center; border-right: 1px dotted gray;">Unit Price</th>
                                <th style="border: 1px solid black; padding: 2px; text-align: center;">Total</th>
                    """
                
                table_html += """
                            </tr>
                        </thead>
                        <tbody>
                """
                
                # Build Table Rows - One row per supplier (vendor) - include all RFQs
                row_idx = 0
                for rfq in all_rfqs:
                    vendor = rfq.partner_id
                    row_idx += 1
                    is_out_of_spec = rfq.amount_total == 0 or rfq.state == 'cancel'
                    
                    table_html += f"""
                            <tr>
                                <td style="border: 1px solid black; padding: 2px; text-align: center; vertical-align: middle;">
                                    <span>{row_idx}</span>
                                </td>
                                <td style="border: 1px solid black; padding: 2px; vertical-align: middle;">
                                    <span>{vendor.name}</span>
                                </td>
                    """
                    
                    # Fill product columns - showing Unit Price and Total Price
                    for product_line in rec.product_line_ids:
                        prod = product_line.product_id
                        rfq_line = valid_rfq_lines.filtered(
                            lambda l: l.product_id == prod and l.order_id == rfq
                        )
                        
                        stock_status = rfq_line and rfq_line[0].out_of_stock or False
                        is_winning_price = rfq_line and rfq_line[0].id == winning_prices.get(prod.id, False) if rfq_line else False
                        winning_bg_color = 'background-color: #cccccc;' if is_winning_price else ''
                        
                        if stock_status == 'out_of_stock' or stock_status == 'out_of_specification':
                            # Merged cell for out of stock or out of specification
                            status_text = "Out of Stock" if stock_status == 'out_of_stock' else "Out of Specification"
                            table_html += f"""
                                <td colspan="2" style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">{status_text}</span>
                                </td>
                            """
                        elif is_out_of_spec:
                            # Show "Out of Spec" for suppliers with no valid bids
                            table_html += """
                                <td colspan="2" style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">Out of Spec</span>
                                </td>
                            """
                        else:
                            # Separate cells for unit price and total
                            if rfq_line and not is_out_of_spec:
                                unit_price = rfq_line[0].price_unit
                                total_price = rfq_line[0].price_subtotal
                                table_html += f"""
                                <td style="border: 1px solid black; border-right: 1px dotted gray; padding: 2px; text-align: right;">
                                    <span>{unit_price:,.2f}</span>
                                </td>
                                <td style="border: 1px solid black; padding: 2px; text-align: right; {winning_bg_color}">
                                    <span>{total_price:,.2f}</span>
                                </td>
                            """
                            elif is_out_of_spec:
                                table_html += """
                                <td style="border: 1px solid black; border-right: 1px dotted gray; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">Out of Spec</span>
                                </td>
                                <td style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">Out of Spec</span>
                                </td>
                            """
                            else:
                                table_html += """
                                <td style="border: 1px solid black; border-right: 1px dotted gray; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">-</span>
                                </td>
                                <td style="border: 1px solid black; padding: 2px; text-align: center;">
                                    <span style="font-size: 8pt;">-</span>
                                </td>
                            """
                    
                    # Total column
                    if not is_out_of_spec:
                        total_amount = rfq.amount_untaxed or 0
                        table_html += f"""
                                <td style="border: 1px solid black; padding: 2px; text-align: right; vertical-align: middle;">
                                    <span>{total_amount:,.2f}</span>
                                </td>
                        """
                    else:
                        table_html += """
                                <td style="border: 1px solid black; padding: 2px; text-align: center; vertical-align: middle;">
                                    <span style="font-size: 8pt;">-</span>
                                </td>
                        """
                    
                    table_html += """
                            </tr>
                    """
                
                table_html += """
                        </tbody>
                    </table>
                """
            
            table_html += """
                </div>
            """
            
            # Calculate financial summary based on winning suppliers (lowest prices)
            winning_lines_by_supplier = self.env['purchase.order.line']
            for product_line in rec.product_line_ids:
                prod = product_line.product_id
                all_lines_for_product = valid_rfq_lines.filtered(
                    lambda l: l.product_id == prod and not l.out_of_stock and l.price_subtotal > 0
                )
                if all_lines_for_product:
                    winning_line = min(all_lines_for_product, key=lambda l: l.price_subtotal)
                    winning_lines_by_supplier |= winning_line
            
            # Get unique suppliers from winning lines
            winning_suppliers = winning_lines_by_supplier.mapped('order_id.partner_id')
            
            if winning_suppliers:
                # Calculate totals per supplier using ONLY winning lines (not entire RFQ)
                # IMPORTANT: This ensures the summary shows ONLY products each supplier won
                supplier_totals = {}
                has_any_positive_tax = False
                has_any_withholding = False
                for supplier in winning_suppliers:
                    supplier_winning_lines = winning_lines_by_supplier.filtered(
                        lambda l: l.order_id.partner_id == supplier
                    )
                    supplier_rfq = supplier_winning_lines[0].order_id if supplier_winning_lines else False
                    
                    # CRITICAL: Calculate from ONLY winning lines, NOT entire RFQ
                    # Untaxed Amount: Sum of price_subtotal from ALL winning lines for this supplier
                    supplier_total = sum(supplier_winning_lines.mapped('price_subtotal')) if supplier_winning_lines else 0.0
                    
                    # Calculate taxes proportionally from RFQ tax_totals based on winning lines ratio
                    supplier_tax = 0.0
                    supplier_withholding = 0.0
                    
                    if supplier_rfq and supplier_rfq.tax_totals and supplier_rfq.amount_untaxed > 0:
                        # Calculate ratio: winning lines subtotal / total RFQ subtotal
                        winning_subtotal = supplier_total
                        rfq_subtotal = supplier_rfq.amount_untaxed
                        ratio = winning_subtotal / rfq_subtotal if rfq_subtotal > 0 else 0.0
                        
                        # Extract taxes from tax_totals and apply ratio
                        subtotals = supplier_rfq.tax_totals.get('subtotals', [])
                        for subtotal_item in subtotals:
                            tax_groups = subtotal_item.get('tax_groups', [])
                            for tax_group in tax_groups:
                                group_name = (tax_group.get('group_name', '') or '').lower()
                                group_label = (tax_group.get('group_label', '') or '').lower()
                                tax_amount = tax_group.get('tax_amount_currency', 0)
                                # Apply ratio to get proportional tax for winning lines only
                                proportional_tax = tax_amount * ratio
                                
                                # Separate positive taxes from withholding
                                if ('withhold' in group_name or 'withholding' in group_name or 
                                    'withhold' in group_label or 'withholding' in group_label) or tax_amount < 0:
                                    supplier_withholding += abs(proportional_tax)
                                elif proportional_tax > 0:
                                    supplier_tax += proportional_tax
                    
                    # Fallback: if no tax_totals or ratio calculation fails, use line-level price_tax
                    if supplier_tax == 0 and supplier_withholding == 0 and supplier_winning_lines:
                        # Try to compute taxes from line tax_ids
                        for line in supplier_winning_lines:
                            if line.taxes_id:
                                # Compute tax for this line
                                tax_result = line.taxes_id.compute_all(
                                    line.price_unit,
                                    currency=line.currency_id,
                                    quantity=line.product_qty,
                                    product=line.product_id,
                                    partner=line.order_id.partner_id
                                )
                                if tax_result and 'taxes' in tax_result:
                                    for tax_detail in tax_result['taxes']:
                                        tax_amount = tax_detail.get('amount', 0)
                                        tax_name = (tax_detail.get('name', '') or '').lower()
                                        # Check if it's withholding
                                        if 'withhold' in tax_name or tax_amount < 0:
                                            supplier_withholding += abs(tax_amount)
                                        elif tax_amount > 0:
                                            supplier_tax += tax_amount
                    
                    # Final fallback: use price_tax if still no taxes calculated
                    if supplier_tax == 0 and supplier_withholding == 0:
                        total_price_tax = sum(supplier_winning_lines.mapped('price_tax')) if supplier_winning_lines else 0.0
                        if total_price_tax > 0:
                            supplier_tax = total_price_tax
                        elif total_price_tax < 0:
                            supplier_withholding = abs(total_price_tax)
                    
                    # Calculate grand total: Untaxed + Sales/Purchase Taxes - Withholding
                    supplier_grand_total = supplier_total + supplier_tax - supplier_withholding
                    
                    # Check for positive taxes
                    if supplier_tax > 0:
                        has_any_positive_tax = True
                    
                    # Only mark as having withholding if actually found in tax_totals
                    if supplier_withholding > 0:
                        has_any_withholding = True
                    
                    supplier_totals[supplier.id] = {
                        'name': supplier.name,
                        'total': supplier_total,
                        'tax': supplier_tax,
                        'withholding': supplier_withholding,
                        'grand_total': supplier_grand_total
                    }
                
                # Add financial summary table with separate columns for each supplier
                # IMPORTANT: This summary shows ONLY the products each supplier WON (lowest price per product)
                # NOT all products in their RFQ quotation
                table_html += """
                    <div style="margin-top: 20px; text-align: right;">
                        <div style="display: inline-block; width: auto;">
                            <table style="width: auto; min-width: 300px; border-collapse: collapse; border: 1px solid black;">
                            <tr>
                """
                
                # Header row with supplier names (each spans 2 columns)
                for supplier in winning_suppliers:
                    table_html += f"""
                                <td colspan="2" style="border: 1px solid black; padding: 5px; text-align: center; font-weight: bold; background-color: #f0f0f0;">
                                    <span>{supplier.name}</span>
                                </td>
                    """
                
                table_html += """
                            </tr>
                """
                
                # For each supplier, create rows with label and value
                # Untaxed Amount row
                table_html += """
                            <tr>
                """
                for supplier in winning_suppliers:
                    supplier_total = supplier_totals[supplier.id]['total']
                    table_html += f"""
                                <td style="border: 1px solid black; padding: 5px;">Untaxed Amount</td>
                                <td style="border: 1px solid black; padding: 5px; text-align: right;">
                                    <span>{supplier_total:,.2f}</span>
                                </td>
                    """
                table_html += """
                            </tr>
                """
                
                # Sales / Purchase Taxes row - Only show if there are positive taxes
                if has_any_positive_tax:
                    table_html += """
                                <tr>
                    """
                    for supplier in winning_suppliers:
                        supplier_tax = supplier_totals[supplier.id]['tax']
                        table_html += f"""
                                    <td style="border: 1px solid black; padding: 5px;">Sales / Purchase Taxes</td>
                                    <td style="border: 1px solid black; padding: 5px; text-align: right;">
                                        <span>{supplier_tax:,.2f}</span>
                                    </td>
                        """
                    table_html += """
                                </tr>
                    """
                
                # Withholding Taxes row - Only show if there are actual withholding taxes
                if has_any_withholding:
                    table_html += """
                                <tr>
                    """
                    for supplier in winning_suppliers:
                        supplier_withholding = supplier_totals[supplier.id]['withholding']
                        withholding_display = f"-{supplier_withholding:,.2f}" if supplier_withholding > 0 else f"{supplier_withholding:,.2f}"
                        table_html += f"""
                                    <td style="border: 1px solid black; padding: 5px;">Withholding Taxes</td>
                                    <td style="border: 1px solid black; padding: 5px; text-align: right;">
                                        <span>{withholding_display}</span>
                                    </td>
                        """
                    table_html += """
                                </tr>
                    """
                
                # Total row
                table_html += """
                            <tr style="font-weight: bold; border-top: 1px solid #000;">
                """
                for supplier in winning_suppliers:
                    supplier_grand_total = supplier_totals[supplier.id]['grand_total']
                    table_html += f"""
                                <td style="border: 1px solid black; padding: 5px;">Total</td>
                                <td style="border: 1px solid black; padding: 5px; text-align: right;">
                                    <span>{supplier_grand_total:,.2f}</span>
                                </td>
                    """
                table_html += """
                            </tr>
                        </table>
                        </div>
                    </div>
                """
            
            rec.comparison_table = table_html


    def action_create_direct_purchase_order(self):
        """
        Opens a new Purchase Order form with pre-filled values based on the current Request,
        inheriting attributes from the selected direct_purchase_id for matching products.
        """
        self.ensure_one()

        if not self.direct_purchase_id:
            raise UserError(_("Please select a Direct Purchase Order first."))

        if not self.product_line_ids:
            raise UserError(_("There are no product lines in this purchase request."))

        direct_po = self.direct_purchase_id

        po_line_mapping = {}
        for line in direct_po.order_line:
            if line.product_id and line.product_id.id not in po_line_mapping:
                po_line_mapping[line.product_id.id] = line

        new_po_lines = []
        for req_line in self.product_line_ids:
            product_id = req_line.product_id.id
            
            if product_id in po_line_mapping:
                ref_line = po_line_mapping[product_id]

                line_vals = {
                    'product_id': product_id,
                    'name': req_line.description or req_line.product_id.display_name,
                    'product_qty': req_line.product_qty,
                    'product_uom': req_line.product_uom.id if req_line.product_uom else ref_line.product_uom.id,
                    'price_unit': ref_line.price_unit,
                }

                if ref_line.taxes_id:
                    line_vals['taxes_id'] = [Command.set(ref_line.taxes_id.ids)]

                # Command.create adds the (0, 0, values) tuple, which is exactly what the context expects
                new_po_lines.append(Command.create(line_vals))

        if not new_po_lines:
            raise UserError(_("None of the products in this request match the products in the selected Direct Purchase Order."))

        # Build context dictionary with default values
        action_context = {
            'default_partner_id': direct_po.partner_id.id,
            'default_rfp_id': self.id,
            'default_origin': self.rfp_number,
            'default_currency_id': direct_po.currency_id.id,
            'default_purchase_origin': self.purchase_origin,
            'default_final_po': True,
            'default_order_line': new_po_lines,
        }

        if hasattr(direct_po, 'applied_tax_ids') and direct_po.applied_tax_ids:
            action_context['default_applied_tax_ids'] = [Command.set(direct_po.applied_tax_ids.ids)]
            
        if hasattr(direct_po, 'price_tax_included'):
            action_context['default_price_tax_included'] = direct_po.price_tax_included

        return {
            'name': _('Create Direct Purchase Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',
            'context': action_context,
        }