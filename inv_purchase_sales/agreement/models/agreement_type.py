# Copyright (C) 2018 - TODAY, Pavlov Media
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AgreementType(models.Model):
    _name = "agreement.type"
    _description = "Agreement Types"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    description=fields.Text(string="Description")
  