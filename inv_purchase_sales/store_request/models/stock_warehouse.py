from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    _description = 'stock.warehouse'

    storeman_id = fields.Many2one('res.users', string="Storeman")
