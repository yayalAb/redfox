from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RfpSplitWizard(models.TransientModel):
    _name = 'rfp.split.wizard'
    _description = 'RFP Split Wizard'

    rfp_id = fields.Many2one(
        'supplies.rfp', 
        string='RFP to Split', 
        required=True,
        readonly=True
    )
    product_line_ids = fields.One2many(
        'rfp.split.wizard.line',
        'wizard_id',
        string='Product Lines'
    )
    re_evaluation = fields.Boolean(
        string="Re-evaluation", 
        default=False,
        help="Check this if the items are being re-evaluated due to supplier failure. "
             "This will duplicate the items and quotations to a new RFP without altering the original."
    )
    evaluation_reason = fields.Text(string="Reason for Re-evaluation")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id') and 'rfp_id' in fields_list:
            rfp_id = self.env.context.get('active_id')
            res['rfp_id'] = rfp_id
            rfp = self.env['supplies.rfp'].browse(rfp_id)
            if not rfp.product_line_ids:
                raise UserError(_('No product lines to split.'))
            
            # Create wizard lines from RFP product lines
            lines = []
            for line in rfp.product_line_ids:
                # Skip lines without products
                if not line.product_id:
                    continue
                    
                lines.append((0, 0, {
                    'product_line_id': line.id,
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name or '',
                    'description': line.description or '',
                    'product_qty': float(line.product_qty) if line.product_qty else 0.0,
                    'product_uom': line.product_uom.id if line.product_uom else False,
                    'split_qty': 0.0,  # User will specify how much to split
                    'keep_in_original': True,  # By default, keep in original
                }))
            res['product_line_ids'] = lines
        return res

    def action_split_rfp(self):
        self.ensure_one()
        if not self.product_line_ids:
            raise UserError(_('Please select products to split.'))
        
        # Validate that at least one product is selected for split
        split_lines = self.product_line_ids.filtered(lambda l: l.split_qty > 0)
        if not split_lines:
            raise UserError(_('Please specify quantities to split for at least one product.'))
        
        # Validate quantities - get original quantity from source product line
        for line in split_lines:
            # Get original quantity from the source product line, not from wizard line
            if not line.product_line_id:
                raise ValidationError(_('Missing product line reference. Please close and reopen the wizard.'))
            
            # Reload the source product line to get current quantity
            original_qty = line.product_line_id.product_qty
            
            # Get product name from product_id if available, otherwise use product_name field
            if line.product_id:
                product_display = line.product_id.name
            elif line.product_name:
                product_display = line.product_name
            else:
                product_display = _('Unknown Product')
            
            # Check if split quantity exceeds original quantity
            if line.split_qty > original_qty:
                difference = line.split_qty - original_qty
                # Only raise error if difference is >= 1.0
                if difference >= 1.0:
                    raise ValidationError(_('Split quantity (%s) cannot be greater than original quantity (%s) for product %s.') % (line.split_qty, original_qty, product_display))
                # If difference is < 1.0, allow it (no error)
            if line.split_qty <= 0:
                raise ValidationError(_('Split quantity must be greater than 0 for product %s.') % product_display)
        
        # Get original RFP
        original_rfp = self.rfp_id

        new_state = 'evaluation' if self.re_evaluation else original_rfp.state
        
        # Create new RFP with split products
        new_rfp_vals = {
            'product_category_id': original_rfp.product_category_id.id,
            'purchase_origin': original_rfp.purchase_origin,
            'purchase_type': original_rfp.purchase_type,
            'department_id': original_rfp.department_id.id,
            'company_id': original_rfp.company_id.id,
            'purpose': original_rfp.purpose,
            'required_date': original_rfp.required_date,
            'state': new_state,
            'store_request_id': original_rfp.store_request_id.id if original_rfp.store_request_id else False,
            'internal_notes': (original_rfp.internal_notes or '') + (f"\nRe-evaluation: {self.evaluation_reason}" if self.evaluation_reason else ""),
            'product_line_ids': [],
        }
        
        # Copy committee members from original RFP to new RFP
        committee_member_commands = []
        for member in original_rfp.committee_member_ids:
            committee_member_commands.append((0, 0, {
                'member_id': member.member_id.id,
                'role': member.role,
                'approval_status': 'pending',  # Reset approval status for new RFP
                'approval_date': False,
            }))
        if committee_member_commands:
            new_rfp_vals['committee_member_ids'] = committee_member_commands
        
        # Add split products to new RFP
        for line in split_lines:
            # Get values from the original product line - this is the source of truth
            original_line = line.product_line_id
            if not original_line:
                raise UserError(_('Original product line reference is missing. Please close and reopen the wizard.'))
            
            # Ensure product_id exists in the original line
            if not original_line.product_id:
                product_display = line.product_name or _('Unknown Product')
                raise UserError(_('Product is missing in the original product line for %s. Please check the RFP.') % product_display)
            
            new_rfp_vals['product_line_ids'].append((0, 0, {
                'product_id': original_line.product_id.id,  # Always use original line's product_id
                'description': original_line.description or '',
                'product_qty': line.split_qty,
                'product_uom': original_line.product_uom.id if original_line.product_uom else False,
                'unit_price': original_line.unit_price or 0.0,
            }))
        
        # Create new RFP
        new_rfp = self.env['supplies.rfp'].create(new_rfp_vals)
        
        # Update original RFP - reduce quantities
        # for line in split_lines:
        #     # Get original quantity from source product line
        #     original_qty = line.product_line_id.product_qty
        #     remaining_qty = original_qty - line.split_qty
            
        #     if remaining_qty > 0:
        #         # Update quantity in original RFP
        #         line.product_line_id.write({'product_qty': remaining_qty})
        #     else:
        #         # If all quantity is split, remove the line from original RFP
        #         line.product_line_id.unlink()
        




        # Handle Post-Creation Logic based on Re-evaluation status
        if self.re_evaluation:
            # === RE-EVALUATION CASE ===
            # 1. Copy Quotations
            self._copy_quotations_to_new_rfp(original_rfp, new_rfp, split_lines)
            
            # 2. Add Note (Do NOT reduce quantities or delete lines in original RFP)
            original_rfp.message_post(
                body=_('Re-evaluation initiated. Created new RFP %s for %s product(s). Reason: %s') % 
                     (new_rfp.rfp_number, len(split_lines), self.evaluation_reason)
            )
        else:
            for line in split_lines:
                original_qty = line.product_line_id.product_qty
                remaining_qty = original_qty - line.split_qty
                
                if remaining_qty > 0:
                    # Update quantity in original RFP
                    line.product_line_id.write({'product_qty': remaining_qty})
                else:
                    # If all quantity is split, remove the line from original RFP
                    line.product_line_id.unlink()


                    
            
            # Add a note to the original RFP
            original_rfp.message_post(
                body=_('RFP split: Created new RFP %s with %s product(s).') % (new_rfp.rfp_number, len(split_lines))
            )

        # # Add a note to the original RFP
        # original_rfp.message_post(
        #     body=_('RFP split: Created new RFP %s with %s product(s).') % (new_rfp.rfp_number, len(split_lines))
        # )
        
        # Add a note to the new RFP
        new_rfp.message_post(
            body=_('This RFP was created by splitting from RFP %s.') % original_rfp.rfp_number
        )
        
        # Return action to view the new RFP
        return {
            'name': _('Split RFP'),
            'type': 'ir.actions.act_window',
            'res_model': 'supplies.rfp',
            'view_mode': 'form',
            'res_id': new_rfp.id,
            'target': 'current',
        }

    def _copy_quotations_to_new_rfp(self, original_rfp, new_rfp, split_lines):
        """Copy RFQs containing the split products to the new RFP."""
        # Get the list of product IDs involved in the split
        product_ids = [l.product_line_id.product_id.id for l in split_lines]
        
        # Find existing RFQs attached to the original RFP
        original_rfqs = self.env['purchase.order'].search([('rfp_id', '=', original_rfp.id)])
        
        for old_po in original_rfqs:
            # Check if this PO contains any of the products being re-evaluated
            relevant_lines = old_po.order_line.filtered(lambda l: l.product_id.id in product_ids)
            
            if not relevant_lines:
                continue

            # Copy the PO Header
            new_po = old_po.copy({
                'rfp_id': new_rfp.id,
                'origin': f"Re-eval: {old_po.name}",
                'state': 'draft',
                'order_line': False, # We will create lines manually to filter specific products
            })

            # Copy only the relevant lines
            for line in relevant_lines:
                line.copy({
                    'order_id': new_po.id,
                    'rfp_id': new_rfp.id, 
                })


class RfpSplitWizardLine(models.TransientModel):
    _name = 'rfp.split.wizard.line'
    _description = 'RFP Split Wizard Line'

    wizard_id = fields.Many2one(
        'rfp.split.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    product_line_id = fields.Many2one(
        'supplies.rfp.product.line',
        string='Original Product Line',
        required=True,
        readonly=False
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        readonly=True
    )
    product_name = fields.Char(
        string='Product Name',
        readonly=True
    )
    description = fields.Text(
        string='Description',
        readonly=True
    )
    product_qty = fields.Float(
        string='Original Quantity',
        digits='Product Unit of Measure',
        readonly=True
    )
    product_uom = fields.Many2one(
        'uom.uom',
        string='UOM',
        readonly=True
    )
    split_qty = fields.Float(
        string='Quantity to Split',
        digits='Product Unit of Measure',
        default=0.0,
        help='Enter the quantity to move to the new RFP. Remaining quantity will stay in the original RFP.'
    )
    keep_in_original = fields.Boolean(
        string='Keep in Original',
        default=True,
        help='If checked, the product will remain in the original RFP with reduced quantity.'
    )

    @api.onchange('split_qty')
    def _onchange_split_qty(self):
        if self.split_qty and self.product_qty and self.split_qty > self.product_qty:
            difference = self.split_qty - self.product_qty
            # Only adjust and show warning if difference is >= 1
            if difference >= 1.0:
                # Reset split_qty if it exceeds original quantity significantly
                self.split_qty = min(self.split_qty, self.product_qty)
                return {
                    'warning': {
                        'title': _('Invalid Quantity'),
                        'message': _('Split quantity cannot exceed original quantity (%s). It has been adjusted to %s.') % (self.product_qty, self.split_qty)
                    }
                }
            # If difference is < 1, keep the entered value (don't adjust)

