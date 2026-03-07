# -*- coding: utf-8 -*-
from odoo import models, fields, api

# --- 1. CONFIGURATION: RISK CATEGORY ---
class CorporateRiskCategory(models.Model):
    _name = 'corporate.risk.category'
    _description = 'Risk Category'

    name = fields.Char(string='Category Name', required=True, translate=True)
    description = fields.Text(string='Description')

# --- 2. MAIN MODEL: RISK REGISTER ---
class CorporateRiskRegister(models.Model):
    _name = 'corporate.risk.register'
    _description = 'Operational Risk Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Risk Description', required=True, tracking=True)
    color = fields.Integer(string='Color Index') 
    # --- CONTEXT ---
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # --- ASSESSMENT ---
    category_id = fields.Many2one('corporate.risk.category', string='Category', required=True)
    
    likelihood = fields.Selection([
        ('1', '1 - Low'),
        ('2', '2 - Medium'),
        ('3', '3 - High')
    ], string='Likelihood', required=True, default='1')

    impact = fields.Selection([
        ('1', '1 - Low'),
        ('2', '2 - Medium'),
        ('3', '3 - High')
    ], string='Impact', required=True, default='1')

    risk_score = fields.Integer(string='Risk Score (L x I)', compute='_compute_risk_score', store=True)
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('significant', 'Significant'),
        ('critical', 'Critical')
    ], string='Risk Level', compute='_compute_risk_score', store=True)

    # --- MITIGATION ---
    mitigation_plan = fields.Html(string='Mitigation / Control Measures')
    responsible_owner_id = fields.Many2one('hr.employee', string='Responsible Owner')
    monitoring_mechanism = fields.Text(string='Monitoring / Reporting Mechanism')
    
    mitigation_priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('immediate', 'Immediate')
    ], string='Mitigation Priority', default='low')

    # --- TRACKING ---
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('mitigated', 'Mitigated'),
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)

    @api.depends('likelihood', 'impact')
    def _compute_risk_score(self):
        for risk in self:
            # Convert selection strings to integers for calculation
            l = int(risk.likelihood) if risk.likelihood else 0
            i = int(risk.impact) if risk.impact else 0
            
            score = l * i
            risk.risk_score = score

            # Determine Risk Level based on Score Range
            if score >= 9:
                risk.risk_level = 'critical'
            elif score >= 6:
                risk.risk_level = 'significant'
            elif score >= 4:
                risk.risk_level = 'moderate'
            else:
                risk.risk_level = 'low'