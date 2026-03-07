from odoo import models, fields, api

class AnnualPlan(models.Model):
    _name = 'corporate.planning.annual.plan'
    _description = 'Corporate Planning Annual Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Title', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    start_date = fields.Date(string='Budget Year Start Date', required=True, tracking=True)
    end_date = fields.Date(string='Budget Year End Date', required=True, tracking=True)
    
    department_id = fields.Many2one('hr.department', string='Prepared By')
    
    preparation_date = fields.Date(string='Preparation Date', readonly=True, default=fields.Date.context_today)
    
    strategy_type_id = fields.Many2one(
        'corporate.strategy.type', 
        string='Strategy Used',
        help="The overarching business strategy applied in this plan."
    )
    
    budget_id = fields.Many2one(
        'budget.analytic', 
        string='Approved Master Budget',
        domain="[('company_id', '=', company_id)]",
        help="Select the final approved budget record from Accounting."
    )

    # --- 2. COMPUTED TOTAL ---
    # We fetch the total from the budget lines
    linked_budget_total = fields.Float(
        string="Total Approved Budget", 
        compute='_compute_budget_total', 
        store=True,
        tracking=True
    )
    
    # budget_plan_id = fields.Many2one('corporate.planning.budget', string='Budget')
    kpi_id = fields.Many2many('appraisal.kpi', string='KPI')
    kpi_category = fields.Many2many('appraisal.kpi.category', string='KPI Category')
    executive_summary = fields.Html(string='Executive Summary')

    alignment_goal = fields.Html(string='Alignment with Organizational Goal')

    key_pillars = fields.Html(string='Key Pillars and Objectives')

    risk_mitigation_ids = fields.One2many('corporate.planning.risk.mitigation', 'annual_plan_id', string='Risks and Mitigations')
    
    performance_measure_ids = fields.One2many('corporate.planning.performance.measure', 'annual_plan_id', string='Performance Measurement Standards')

    conclusion = fields.Html(string='Conclusion')
    
    linked_budget_name = fields.Char(string="Budget Name", compute='_compute_budget_info')
    
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    def action_approve(self):
        self.write({'state': 'approved'})
    def action_reset_draft(self):
        self.write({'state': 'draft'})
    def action_cancel(self):
        self.write({'state': 'cancelled'})
        
    @api.onchange('kpi_category')
    def _onchange_kpi_category_ids(self):
        if self.kpi_category:
            # All selected category IDs
            category_ids = self.kpi_category.ids
            
            # Get all KPIs matching ANY of these categories
            kpis = self.env['appraisal.kpi'].search([('Kpi_category', 'in', category_ids)])
            
            # Auto-fill the KPI list
            self.kpi_id = [(6, 0, kpis.ids)]
        else:
            # If no categories selected → clear KPIs
            self.kpi_id = [(5, 0, 0)]


    @api.depends('budget_id')
    def _compute_budget_total(self):
        for plan in self:
            if plan.budget_id:
                
                lines = self.env['budget.line'].search([
                    ('budget_analytic_id', '=', plan.budget_id.id)
                ])
                
                # Summing the 'budget_amount' field we used in previous steps
                total = sum(lines.mapped('budget_amount'))
                plan.linked_budget_total = total
            else:
                plan.linked_budget_total = 0.0
class RiskMitigation(models.Model):
    _name = 'corporate.planning.risk.mitigation'
    _description = 'Risk and Mitigation Line Item'
    _order = 'sequence, id'

    annual_plan_id = fields.Many2one('corporate.planning.annual.plan', string='Annual Plan')
    
    sequence = fields.Integer(string='Sequence', default=10)
    
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')
    ], default=False, help="Technical field for UX purpose.")
    
    name = fields.Char(string="Section Name") 

    risk = fields.Text(string='Risk')
    mitigation = fields.Text(string='Mitigation')


class PerformanceMeasure(models.Model):
    _name = 'corporate.planning.performance.measure'
    _description = 'Performance Measurement Standard Line'
    _order = 'sequence, id'

    annual_plan_id = fields.Many2one('corporate.planning.annual.plan', string='Annual Plan')
    sequence = fields.Integer(string='Sequence', default=10)

    category = fields.Char(string='Category')
    weight = fields.Float(string='Weight (%)')
    metric = fields.Char(string='Metric') 
    remark = fields.Char(string='Remark')