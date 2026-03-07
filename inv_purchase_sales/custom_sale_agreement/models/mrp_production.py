from odoo import models, fields

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    agreement_id = fields.Many2one(
        'sale.agreement',
        string='Contract Agreement',
        copy=False,
        index=True,
        readonly=True
    )
    quality_document_ids = fields.Many2many(
        'ir.attachment',
        string='Quality Approval Documents',
        copy=False,
    )