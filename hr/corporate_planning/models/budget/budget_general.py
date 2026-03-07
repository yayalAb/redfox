# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BudgetGeneralType(models.Model):
    _name = 'corporate.planning.budget.type'
    _description = 'Budget Type Configuration'
    
    name = fields.Char(string='Budget Type Name', required=True, translate=True)
    
    # This determines which columns show up (Asset style vs Recurring style)
    category = fields.Selection([
        ('recurring', 'Recurring (Monthly Based)'),
        ('asset', 'Fixed Asset (Quantity Based)')
    ], string='Behavior Category', required=True, default='recurring',
      help="Select 'Recurring' for items like cleaning/entertainment. Select 'Fixed Asset' to enable Stock No and hide Monthly calc.")
class BudgetGeneralPlan(models.Model):
    _name = 'corporate.planning.budget.general'
    _description = 'General Service & Asset Budget Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Plan Title', required=True, default='New Budget Plan')
    
    budget_type_id = fields.Many2one('corporate.planning.budget.type', string='Budget Type', required=True)
    
    budget_category = fields.Selection(related='budget_type_id.category', string='Category', store=True, readonly=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Department', required=True)

    fiscal_year = fields.Char(string='Budget Year', required=True, default=lambda self: str(fields.Date.today().year + 1))
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account', 
        required=True
    )
    linked_budget_id = fields.Many2one(
        'budget.analytic', 
        string='Add to Existing Budget',
        domain="[('company_id', '=', company_id)]"
    )
    
    line_ids = fields.One2many('corporate.planning.budget.general.line', 'plan_id', string='Budget Lines')
    
    note = fields.Html(string='Notes / Justification')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    total_annual_amount = fields.Float(string='Total Annual Budget', compute='_compute_total', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    @api.depends('line_ids.total_price_annual')
    def _compute_total(self):
        for plan in self:
            plan.total_annual_amount = sum(line.total_price_annual for line in plan.line_ids)

    # Workflow Actions
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    def action_approve(self):
        self.write({'state': 'approved'})
        self._create_analytic_budget()
    def action_reset_draft(self):
        self.write({'state': 'draft'})
    def action_cancel(self):
        self.write({'state': 'cancelled'})
        
    def _create_analytic_budget(self):
        if 'budget.analytic' not in self.env or 'budget.line' not in self.env:
            return

        BudgetParent = self.env['budget.analytic']
        BudgetLine = self.env['budget.line']

        for plan in self:
            if not plan.analytic_account_id:
                continue

            if plan.linked_budget_id:
                budget_id = plan.linked_budget_id.id
            else:
                parent_vals = {
                    'name': f"{plan.name} ({plan.fiscal_year})",
                    'date_from': plan.date_from,
                    'date_to': plan.date_to,
                    'company_id': plan.company_id.id,
                }
                new_budget = BudgetParent.create(parent_vals)
                budget_id = new_budget.id

            line_vals = {
                'budget_analytic_id': budget_id,
                'account_id': plan.analytic_account_id.id,
                'budget_amount': plan.total_annual_amount,
                'date_from': plan.date_from,
                'date_to': plan.date_to,
                'company_id': plan.company_id.id,
            }
            BudgetLine.create(line_vals)
            plan.message_post(body=f"✅ General Budget integrated.")


class BudgetGeneralLine(models.Model):
    _name = 'corporate.planning.budget.general.line'
    _description = 'General Budget Line Item'
    _order = 'sequence, id'

    plan_id = fields.Many2one('corporate.planning.budget.general', string='Budget Plan')
    sequence = fields.Integer(string='No', default=10)
    
    # 1. Product / Description
    # We can link to a product if available, or just use text
    product_id = fields.Many2one('product.product', string='Product (Optional)')
    description = fields.Char(string='Description of Materials', required=True)
    
    # 2. Identification (Specific to Fixed Assets)
    stock_no = fields.Char(string='Stock No.')

    # 3. Unit Info
    uom_id = fields.Many2one('uom.uom', string='Unit')
    
    # 4. Pricing
    unit_price = fields.Float(string='Unit Price (Birr)', required=True, default=0.0)
    estimated_price = fields.Float(string='Estimated Price (with markup)', help="Unit Price + Contingency if needed")
    
    # 5. Monthly Calculation (Specific to Entertainment/Cleaning)
    qty_monthly = fields.Float(string='Monthly Qty', default=0.0)
    total_price_monthly = fields.Float(string='Monthly Total', compute='_compute_monthly', store=True)
    
    # 6. Annual Calculation (For Fixed Assets OR calculated from Monthly)
    qty_annual = fields.Float(string='Annual Qty', compute='_compute_annual_qty', store=True, readonly=False)
    total_price_annual = fields.Float(string='Annual Total Price', compute='_compute_annual_total', store=True)
    
    remark = fields.Char(string='Remarks')

    # --- AUTO-FILL DESCRIPTION IF PRODUCT SELECTED ---
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.uom_id = self.product_id.uom_id
            self.unit_price = self.product_id.standard_price

    # --- COMPUTATIONS ---
    
    @api.depends('qty_monthly', 'estimated_price', 'unit_price')
    def _compute_monthly(self):
        for line in self:
            price = line.estimated_price if line.estimated_price > 0 else line.unit_price
            line.total_price_monthly = line.qty_monthly * price

    @api.depends('qty_monthly', 'plan_id.budget_type_id')
    def _compute_annual_qty(self):
        for line in self:
            # If it's a recurring expense (Entertainment/Cleaning), Annual = Monthly * 12
            # If it's Fixed Asset, we usually enter Annual Qty manually (so we don't overwrite if user typed it)
            if line.plan_id.budget_type_id in ['entertainment', 'cleaning']:
                line.qty_annual = line.qty_monthly * 12
            # For fixed assets, we leave it as is (0 or user input)
            else:
                if line.qty_annual == 0:
                    line.qty_annual = line.qty_monthly # fallback

    @api.depends('qty_annual', 'estimated_price', 'unit_price')
    def _compute_annual_total(self):
        for line in self:
            price = line.estimated_price if line.estimated_price > 0 else line.unit_price
            line.total_price_annual = line.qty_annual * price