# -*- coding: utf-8 -*-
from odoo import models, fields


class LcLetterStage(models.Model):
    _name = 'lc.letter.stage'
    _description = 'LC Letter Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    fold = fields.Boolean(
        string='Folded in Kanban',
        help='Fold this stage in the kanban view when there are no records.',
    )
