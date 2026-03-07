# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CrmSector(models.Model):
    _name = 'crm.sector'
    _description = 'Business Sector'
    _order = 'name'

    name = fields.Char(string='Sector Name', required=True, translate=True)
    description = fields.Text(string='Description')
    # This allows you to see linked industries from the Sector form, if needed.
    industry_ids = fields.One2many('crm.industry', 'sector_id', string='Industries')

class CrmIndustry(models.Model):
    _name = 'crm.industry'
    _description = 'Business Industry'
    _order = 'name'

    name = fields.Char(string='Industry Name', required=True, translate=True)
    sector_id = fields.Many2one('crm.sector', string='Sector', required=True, ondelete='cascade')
    description = fields.Text(string='Description')