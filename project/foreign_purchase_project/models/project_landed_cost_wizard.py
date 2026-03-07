from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectLandedCostWizard(models.TransientModel):
    _name = 'project.landed.cost.wizard'
    _description = 'Wizard to Create Landed Cost from Project'

    project_id = fields.Many2one('project.project', string='Project', required=True)
    product_id = fields.Many2one(
        'product.product', 
        string='Product', 
        required=True, 
        domain=[('landed_cost_ok', '=', True)]
    )
    amount = fields.Float(string='Amount', required=True)

    def action_create_landed_cost(self):
        self.ensure_one()
        
        po = self.project_id.purchase_order_ids[:1]
        if not po:
            raise UserError(_("There is no Purchase Order attached to this project."))

        bills = po.invoice_ids.filtered(lambda m: m.move_type == 'in_invoice')
        if not bills:
            raise UserError(_("There is no vendor bill created for the attached Purchase Order."))

        draft_bills = bills.filtered(lambda b: b.state == 'draft')
        if not draft_bills:
            raise UserError(_("There are no draft vendor bills for this Purchase Order. Please reset the existing bill to draft or create a new draft bill."))

        target_bill = draft_bills[0]

        # 4. Add the product line to the vendor bill
        target_bill.write({
            'invoice_line_ids':[(0, 0, {
                'product_id': self.product_id.id,
                'quantity': 1,
                'price_unit': self.amount,
                'is_landed_costs_line': True, 
            })]
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': target_bill.id,
            'view_mode': 'form',
            'target': 'current',
            
        }