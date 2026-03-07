from odoo import models, fields, api
class AppraisalKpiCategory(models.Model):
    _name = 'appraisal.kpi.category'
    _description = 'KPI Category'
    
    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')