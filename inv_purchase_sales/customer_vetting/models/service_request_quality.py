# -*- coding: utf-8 -*-
from odoo import fields, models


class ServiceRequestQuality(models.Model):
    _name = 'service.request.quality'
    _description = 'Service Request Quality'
    _order = 'sequence, name'

    name = fields.Char(string='Quality', required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    description = fields.Text()
