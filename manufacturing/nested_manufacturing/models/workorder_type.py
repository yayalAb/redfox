from odoo import models, fields, api

class WorkOrderTypes(models.Model):
    _name = 'workorder.type'

    name = fields.Char(string='Work Order Type', required=True)
    description = fields.Text(string='Description')
    

