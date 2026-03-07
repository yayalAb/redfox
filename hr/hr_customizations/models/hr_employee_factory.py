# -*- coding: utf-8 -*-
from odoo import models, fields

class EmployeeFactory(models.Model):
    _name = 'hr.employee.factory'
    _description = 'Employee Factory'
    _order = 'name'

    name = fields.Char(string='Factory Name', required=True, index=True)
    address_id = fields.Many2one('res.partner', string='Address')

    # might add factory manager later