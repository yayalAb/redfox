# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # --- Manual Year Field ---
    fiscal_year_for_sequence = fields.Char(
        related='company_id.fiscal_year_for_sequence',
        string="Current Fiscal Year",
        readonly=False,
        help="Set the year used for all document sequences."
    )

    # --- External Sequence Fields ---
    external_ref_sequence_id = fields.Many2one(
        related='company_id.external_ref_sequence_id',
        string='External Document Sequence',
        readonly=False
    )
    external_sequence_preview = fields.Char(
        string='External Sequence Preview',
        compute='_compute_sequence_previews',
    )
    external_sequence_number_next = fields.Integer(
        string='External Next Number',
        compute='_compute_sequence_number_next',
        inverse='_inverse_sequence_number_next',
    )

    # --- Internal Sequence Fields ---
    internal_ref_sequence_id = fields.Many2one(
        related='company_id.internal_ref_sequence_id',
        string='Internal Document Sequence',
        readonly=False
    )
    internal_sequence_preview = fields.Char(
        string='Internal Sequence Preview',
        compute='_compute_sequence_previews',
    )
    internal_sequence_number_next = fields.Integer(
        string='Internal Next Number',
        compute='_compute_sequence_number_next',
        inverse='_inverse_sequence_number_next',
    )


    # --- Compute and Inverse Methods ---

    @api.depends('external_ref_sequence_id', 'internal_ref_sequence_id', 'fiscal_year_for_sequence')
    def _compute_sequence_previews(self):
        """Compute the preview string, including the manually set year."""
        for settings in self:
            # External Preview
            if settings.external_ref_sequence_id and settings.fiscal_year_for_sequence:
                sequence = settings.external_ref_sequence_id
                # This combines the sequence's prefix/padding with the manual year
                base_val = sequence.get_next_char(sequence.number_next_actual)
                year_part = settings.fiscal_year_for_sequence[-2:]
                settings.external_sequence_preview = f"{base_val}/{year_part}"
            else:
                settings.external_sequence_preview = 'N/A'

            # Internal Preview
            if settings.internal_ref_sequence_id and settings.fiscal_year_for_sequence:
                sequence = settings.internal_ref_sequence_id
                base_val = sequence.get_next_char(sequence.number_next_actual)
                year_part = settings.fiscal_year_for_sequence
                settings.internal_sequence_preview = f"{base_val}/{year_part}"
            else:
                settings.internal_sequence_preview = 'N/A'


    @api.depends('external_ref_sequence_id', 'internal_ref_sequence_id')
    def _compute_sequence_number_next(self):
        """Read the 'number_next_actual' from the selected sequence."""
        for settings in self:
            settings.external_sequence_number_next = settings.external_ref_sequence_id.number_next_actual or 1
            settings.internal_sequence_number_next = settings.internal_ref_sequence_id.number_next_actual or 1

    def _inverse_sequence_number_next(self):
        """Write the 'number_next_actual' back to the sequence upon saving."""
        for settings in self:
            if settings.external_ref_sequence_id and settings.external_sequence_number_next:
                settings.external_ref_sequence_id.sudo().number_next_actual = settings.external_sequence_number_next
            if settings.internal_ref_sequence_id and settings.internal_sequence_number_next:
                settings.internal_ref_sequence_id.sudo().number_next_actual = settings.internal_sequence_number_next