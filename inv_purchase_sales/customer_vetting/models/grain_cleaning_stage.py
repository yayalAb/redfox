# -*- coding: utf-8 -*-
from odoo import fields, models


class GrainCleaningStage(models.Model):
    _name = 'grain.cleaning.stage'
    _description = 'Grain Cleaning Process Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(
        string='Folded',
        help='Folded in Kanban when there are no records in this stage.',
    )
    technical_key = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('reviewed', 'Reviewed'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancel', 'Cancelled'),
        ],
        string='Technical key',
        required=True,
        copy=False,
    )

    _sql_constraints = [
        (
            'grain_cleaning_stage_technical_key_unique',
            'unique(technical_key)',
            'The technical key must be unique per grain cleaning stage.',
        ),
    ]
