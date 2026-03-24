# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    withholding_tax_threshold = fields.Float(
        string='Withholding Tax Threshold',
        config_parameter='withholding_tax_threshold.amount_threshold',
        default=20000.0,
        help="Withholding tax is applied only when the document total (amount before tax) exceeds this value. "
             "Documents with total <= threshold will not have withholding tax applied."
    )
