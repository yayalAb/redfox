from functools import reduce

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import SQL


class ResCompany(models.Model):

    _inherit = 'res.company'
    logo_2 = fields.Binary(
        string='Second Logo',
        help='Second logo for the company, used in various reports and documents.')
