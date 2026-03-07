from odoo import models, fields, api

class CorporateStrategyAnalysis(models.Model):
    _name = 'corporate.strategy.analysis'
    _description = 'Strategic Environment Analysis (PESTEL/SWOT/etc)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Analysis Title', required=True, default='New Strategic Analysis')
    
    # Context
    company_id = fields.Many2one('res.company', string='Business Unit / Company', required=True, default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Department')
    fiscal_year = fields.Char(string='Fiscal Year', required=True, default=lambda self: str(fields.Date.today().year + 1))
    analysis_date = fields.Date(string='Analysis Date', default=fields.Date.context_today)

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved')
    ], string='Status', default='draft', tracking=True)

    # --- RELATIONS TO LOGS ---
    pestel_ids = fields.One2many('corporate.strategy.pestel', 'analysis_id', string='PESTEL Log')
    stakeholder_ids = fields.One2many('corporate.strategy.stakeholder', 'analysis_id', string='Stakeholder Log')
    benchmark_ids = fields.One2many('corporate.strategy.benchmark', 'analysis_id', string='Benchmark Log')
    market_ids = fields.One2many('corporate.strategy.market', 'analysis_id', string='Market Analysis')
    porter_ids = fields.One2many('corporate.strategy.porter', 'analysis_id', string='Porter Five Forces')
    swot_ids = fields.One2many('corporate.strategy.swot', 'analysis_id', string='Internal Strength/Weakness')

    def action_confirm(self):
        self.write({'state': 'confirmed'})
    def action_approve(self):
        self.write({'state': 'approved'})


# --- SECTION B: PESTEL LOG ---
class StrategyPESTEL(models.Model):
    _name = 'corporate.strategy.pestel'
    _description = 'PESTEL Analysis Line'

    analysis_id = fields.Many2one('corporate.strategy.analysis')
    
    factor = fields.Selection([
        ('political', 'Political'),
        ('economic', 'Economic'),
        ('social', 'Social'),
        ('technological', 'Technological'),
        ('environmental', 'Environmental'),
        ('legal', 'Legal')
    ], string='Factor', required=True)
    
    sub_factor = fields.Char(string='Sub-Factor', help="e.g., Trade policy, Inflation")
    current_status = fields.Text(string='Current Status')
    impact_code = fields.Char(string='Influence on P-Q-C-Qi-QI', help="P=Prod, Q=Qual, C=Cost, Qi=Quality?, QI=Innov")
    urgency = fields.Selection([('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], string='Urgency')
    required_action = fields.Char(string='Required Corporate Action')


# --- SECTION C: STAKEHOLDER LOG ---
class StrategyStakeholder(models.Model):
    _name = 'corporate.strategy.stakeholder'
    _description = 'Stakeholder Analysis Line'

    analysis_id = fields.Many2one('corporate.strategy.analysis')
    
    stakeholder_category = fields.Char(string='Stakeholder Category', required=True, help="Gov, Customers, Suppliers...")
    sub_factor = fields.Char(string='Sub-Factor')
    current_status = fields.Text(string='Current Status (Attitude/Behavior)')
    influence_level = fields.Selection([('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], string='Influence Level')
    expected_impact = fields.Char(string='Expected Impact (P-Q-C...)')
    engagement_priority = fields.Selection([('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], string='Engage Priority')
    required_action = fields.Char(string='Required Action')


# --- SECTION D: INDUSTRY BENCHMARK LOG ---
class StrategyBenchmark(models.Model):
    _name = 'corporate.strategy.benchmark'
    _description = 'Benchmark Analysis Line'

    analysis_id = fields.Many2one('corporate.strategy.analysis')
    
    area = fields.Char(string='Benchmark Area', required=True, help="Inventory Accuracy, Order Fulfillment...")
    industry_standard = fields.Char(string='Industry Standard')
    current_status = fields.Char(string='Current Status in BU')
    gap = fields.Char(string='Gap (Std - Actual)')
    impact_code = fields.Char(string='Impact on P-Q-C...')
    urgency = fields.Selection([('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], string='Urgency')
    required_action = fields.Char(string='Required Action')


# --- SECTION E: MARKET ANALYSIS LOG ---
class StrategyMarket(models.Model):
    _name = 'corporate.strategy.market'
    _description = 'Market Analysis Line'

    analysis_id = fields.Many2one('corporate.strategy.analysis')
    
    market_factor = fields.Char(string='Market Factor', required=True)
    current_status = fields.Text(string='Current Status')
    effect_on_bu = fields.Char(string='Effect on BU')
    opportunity_threat = fields.Selection([
        ('opportunity', 'Opportunity'),
        ('threat', 'Threat')
    ], string='Opp/Threat', required=True)
    urgency = fields.Selection([('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], string='Urgency')
    required_action = fields.Char(string='Required Action')
    impact_code = fields.Char(string='Impact on P-Q-C...')


# --- SECTION F: PORTER'S FIVE FORCES ---
class StrategyPorter(models.Model):
    _name = 'corporate.strategy.porter'
    _description = 'Porter Five Forces Line'

    analysis_id = fields.Many2one('corporate.strategy.analysis')
    
    force = fields.Selection([
        ('supplier', 'Supplier Power'),
        ('buyer', 'Buyer Power'),
        ('new_entrants', 'New Entrants'),
        ('substitutes', 'Substitutes'),
        ('rivalry', 'Rivalry')
    ], string='Force', required=True)
    
    sub_factor = fields.Char(string='Sub-Factor')
    current_status = fields.Text(string='Current Status (Intensity)')
    level = fields.Selection([('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], string='Level')
    impact_code = fields.Char(string='Impact on P-Q-C...')
    required_action = fields.Char(string='Required Action')


# --- SECTION G: INTERNAL STRENGTH & WEAKNESS ---
class StrategySWOT(models.Model):
    _name = 'corporate.strategy.swot'
    _description = 'Internal Strength Weakness Line'

    analysis_id = fields.Many2one('corporate.strategy.analysis')
    
    category = fields.Char(string='Category', help="People, Process, Technology, Finance, Assets...")
    factor = fields.Char(string='Factor', required=True)
    current_status = fields.Text(string='Current Status')
    type = fields.Selection([
        ('strength', 'Strength'),
        ('weakness', 'Weakness')
    ], string='Type', required=True)
    impact_code = fields.Char(string='Impact on P-Q-C...')
    priority = fields.Selection([('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], string='Priority')
    required_action = fields.Char(string='Required Action')