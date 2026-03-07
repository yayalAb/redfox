# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class ResCompany(models.Model):
    _inherit = 'res.company'

    external_ref_sequence_id = fields.Many2one(
        'ir.sequence', string='External Reference Sequence')
    internal_ref_sequence_id = fields.Many2one(
        'ir.sequence', string='Internal Reference Sequence')
    company_name_am = fields.Char(
        string='Company Name (Amharic)',)

    # New field to store the year manually
    fiscal_year_for_sequence = fields.Char(
        string="Current Fiscal Year for Sequences",
        # Sensible default for Ethiopian year
        default=lambda self: str(date.today().year - 8),
        help="Manually set the year to be used in document references. E.g., '2016'. "
             "This must be updated manually at the start of each new fiscal year."
    )

    def _get_formatted_sequence(self, doc_type):
        """
        Gets the next number from the sequence and appends the manually set fiscal year.
        This is the new main function to be called from reports.

        :param doc_type: 'internal' or 'external'
        :return: A fully formatted reference string, e.g., "WG/0001/16"
        """
        self.ensure_one()

        if not self.fiscal_year_for_sequence:
            raise UserError(
                _("The 'Current Fiscal Year for Sequences' is not set in General Settings. Please configure it."))

        # Determine which sequence to use
        if doc_type == 'external':
            sequence = self.external_ref_sequence_id
            # Use last 2 digits for the year
            year_part = self.fiscal_year_for_sequence[-2:]
            error_msg = _(
                "The sequence for External References is not configured in General Settings.")
        elif doc_type == 'internal':
            sequence = self.internal_ref_sequence_id
            # Use the full year string
            year_part = self.fiscal_year_for_sequence
            error_msg = _(
                "The sequence for Internal References is not configured in General Settings.")
        else:
            return ''

        if not sequence:
            raise UserError(error_msg)

        # Get the next number in the sequence (e.g., "WG/0001")
        next_val = sequence.next_by_id()

        # Append the year part and return the final string
        return f"{next_val}/{year_part}"
