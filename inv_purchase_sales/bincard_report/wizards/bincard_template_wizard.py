from datetime import timedelta
from odoo import models, fields, api

class BinCardTemplateReportWizard(models.TransientModel):
    _name = 'bincard.template.report.wizard'
    _description = 'Bin Card Report Wizard for Templates'

    # The template is the main record, passed from context
    product_template_id = fields.Many2one(
        'product.template', string='Product Template', required=True,
        default=lambda self: self.env.context.get('active_id'))

    # The user can optionally select a single variant.
    # The domain ensures only variants of the current template can be chosen.
    # If left empty, it means "All Variants".
    product_id = fields.Many2one(
        'product.product', string='Product Variant',
        domain="[('product_tmpl_id', '=', product_template_id)]")

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, 
        default=lambda self: self.env.company)

    location_id = fields.Many2one(
        'stock.location', 
        string='Location (Optional)', 
        domain="[('warehouse_id', '=', warehouse_id), ('usage', '=', 'internal')]",
        help="Leave empty to report on the entire warehouse."
    )
    
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date', default=fields.Date.context_today)

    def _get_header_info(self):
        self.ensure_one()

        bincard_no = self.product_template_id.bincard_no
        # Case 1: A specific variant IS selected by the user.
        # This part of the logic is already correct and does not need to change.
        if self.product_id:
            orderpoint = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', self.product_id.id),
                ('warehouse_id', '=', self.warehouse_id.id),
            ], limit=1)
            return {
                'description': self.product_id.display_name,
                'stock_no': self.product_id.default_code,
                'unit': self.product_id.uom_id.name,
                'min_level': orderpoint.product_min_qty or 0.0,
                'max_level': orderpoint.product_max_qty or 0.0,
                'card_no': bincard_no or 'N/A'
            }
        
        # Case 2: NO specific variant is selected (report on all variants).
        else:
            # ======================= START OF NEW LOGIC =======================
            # Default to a clear signal in case no variants or rules are found.
            min_level = 'N/A'
            max_level = 'N/A'
            stock_no = self.product_template_id.default_code or 'N/A'
            
            # Get the list of variants for the current template
            variants = self.product_template_id.product_variant_ids
            
            # Check if there's at least one variant to avoid errors
            if variants:
                # Automatically select the first variant from the list
                first_variant = variants[0]
                stock_no = first_variant.default_code or self.product_template_id.default_code or 'N/A'
                
                # Find its reordering rule specifically for the selected warehouse
                orderpoint = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id', '=', first_variant.id),
                    ('warehouse_id', '=', self.warehouse_id.id),
                ], limit=1)
                
                # If a rule exists, use its values. Otherwise, default to 0.0.
                # This handles the case where the first variant exists but has no rule.
                min_level = orderpoint.product_min_qty or 0.0
                max_level = orderpoint.product_max_qty or 0.0
            # ======================== END OF NEW LOGIC ========================

            # Return the template's info, but with the dynamically found min/max levels.
            return {
                'description': self.product_template_id.name,
                'stock_no': stock_no,
                'unit': self.product_template_id.uom_id.name,
                'min_level': min_level, # Use the calculated or default 'N/A' value
                'max_level': max_level, # Use the calculated or default 'N/A' value
                'card_no': bincard_no or 'N/A'
            }

    def _get_report_data(self):
        self.ensure_one()
        
        # Step 1: Determine which products to search for
        if self.product_id:
            target_products = self.product_id
        else:
            target_products = self.product_template_id.product_variant_ids
        target_product_ids = target_products.ids

        # Step 2: Determine the set of locations to report on
        if self.location_id:
            target_locations = self.location_id
        else:
            target_locations = self.env['stock.location'].search([
                ('id', 'child_of', self.warehouse_id.view_location_id.id),
                ('usage', '=', 'internal')
            ])
        target_location_ids = target_locations.ids

        # Step 3: Calculate the Opening Balance
        opening_balance = 0.0
        report_lines = []
        
        if self.date_from:
            opening_domain = [
                ('product_id', 'in', target_product_ids), ('state', '=', 'done'),
                ('date', '<', self.date_from),
                '|', ('location_id', 'in', target_location_ids),
                     ('location_dest_id', 'in', target_location_ids),
            ]
            opening_moves = self.env['stock.move.line'].search(opening_domain)
            
            for move in opening_moves:
                # Exclude internal transfers if reporting on the whole warehouse
                if not self.location_id and move.picking_id.picking_type_id.code == 'internal':
                    continue

                src_is_target = move.location_id.id in target_location_ids
                dest_is_target = move.location_dest_id.id in target_location_ids

                if dest_is_target and not src_is_target:
                    opening_balance += move.quantity
                elif src_is_target and not dest_is_target:
                    opening_balance -= move.quantity
        
        # Always add the opening balance line for consistency
        report_lines.append({'is_opening': True, 'date': self.date_from, 'balance': opening_balance})

        # Step 4: Get the main move lines for the selected period
        main_domain = [
            ('product_id', 'in', target_product_ids), ('state', '=', 'done'),
            '|', ('location_id', 'in', target_location_ids),
                 ('location_dest_id', 'in', target_location_ids),
        ]
        if self.date_from:
            main_domain.append(('date', '>=', self.date_from))
        if self.date_to:
            date_to_inclusive = self.date_to + timedelta(days=1)
            main_domain.append(('date', '<', date_to_inclusive))

        move_lines = self.env['stock.move.line'].search(main_domain, order='date asc, id asc')

        total_in, total_out, current_balance = 0.0, 0.0, opening_balance
        for line in move_lines:
            # Exclude internal transfers on warehouse-level reports
            if not self.location_id and line.picking_id.picking_type_id.code == 'internal':
                continue

            src_is_target = line.location_id.id in target_location_ids
            dest_is_target = line.location_dest_id.id in target_location_ids

            qty_in, qty_out = 0.0, 0.0
            if dest_is_target and not src_is_target:
                qty_in = line.quantity
            elif src_is_target and not dest_is_target:
                qty_out = line.quantity
            else:
                continue

            if not qty_in and not qty_out:
                continue

            total_in += qty_in
            total_out += qty_out
            current_balance += qty_in - qty_out
            
            picking = line.picking_id

            partner_display = ''
            if picking and picking.partner_id:
                partner_name = picking.partner_id.name
                if picking.picking_type_id.code == 'outgoing':
                    partner_display = f"{partner_name} (Recipient)"
                elif picking.picking_type_id.code == 'incoming':
                    partner_display = f"{partner_name} (Supplier)"
            
            report_lines.append({
                'is_opening': False, 'date': line.date,
                # This line is crucial for the template-level report!
                # 'variant_name': line.product_id.display_name,
                'grn_no': picking.name if picking.picking_type_id.code == 'incoming' else 'None',
                'siv_no': picking.name if picking.picking_type_id.code == 'outgoing' else 'None',
                'recipient': partner_display, 'qty_in': qty_in,
                'qty_out': qty_out, 'balance': current_balance,
            })
        
        return {
            'lines': report_lines, 'total_in': total_in,
            'total_out': total_out, 'final_balance': current_balance,
        }

    def action_generate_report(self):
        # We need a new report action and template to handle the new 'variant_name' column
        return self.env.ref('bincard_report.action_report_bincard_template_view').report_action(self)