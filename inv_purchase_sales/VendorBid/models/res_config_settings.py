from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    petty_cash_limit = fields.Float(
        string='Petty Cash Limit',
        config_parameter='vendor_bid.petty_cash_limit',
        default=0.0,
        help="Maximum amount allowed for petty cash purchases without additional approval."
    )
    
    ceo_approval_threshold = fields.Float(
        string='CEO Approval Threshold',
        config_parameter='vendor_bid.ceo_approval_threshold',
        default=0.0,
        help="Purchase requests above this amount will require CEO approval. Set to 0 to disable CEO approval requirement."
    )

