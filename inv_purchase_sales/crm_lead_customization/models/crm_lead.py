# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    source = fields.Char(string='Source')
    agreement_count = fields.Integer(compute='_compute_agreement_count', string='Agreement Count')

    # --- Sector & Industry Fields are added ---
    sector_id = fields.Many2one(
        'crm.sector', 
        string='Sector', 
        tracking=True,
        help="High-level business classification"
    )
    
    industry_id = fields.Many2one(
        'crm.industry', 
        string='Industry', 
        tracking=True,
        domain="[('sector_id', '=', sector_id)]", # <--- Key: Filters Industry based on Sector
        help="Specific industry sub-classification"
    )

    # --- Logic: Clear Industry if Sector changes ---
    @api.onchange('sector_id')
    def _onchange_sector_id(self):
        """Reset industry if the sector is changed to prevent invalid combinations"""
        if self.sector_id and self.industry_id:
            if self.industry_id.sector_id != self.sector_id:
                self.industry_id = False

    # ---  Agreement Logic ---
    def _compute_agreement_count(self):
        for lead in self:
            lead.agreement_count = self.env['sale.agreement'].search_count([('lead_id', '=', lead.id)])

    def action_create_new_agreement(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Agreement',
            'res_model': 'sale.agreement',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_name': self.name,
                'default_source_from': 'direct'
            }
        }

    def action_view_agreements(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agreements',
            'res_model': 'sale.agreement',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'target': 'current',
        }