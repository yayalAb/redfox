from odoo import models, fields


class CostCenter(models.Model):
    _name = 'hr.cost.center'
    _rec_name = 'cost_center'

    cost_center = fields.Char(string='Name')
