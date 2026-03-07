from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrAppraisalNote(models.Model):
    _inherit = "hr.appraisal.note"

    # 1st Requirement: Add lower and upper bound fields
    lower_bound = fields.Float(
        string="Lower Bound (%)", required=True, default=0.0)
    upper_bound = fields.Float(
        string="Upper Bound (%)", required=True, default=0.0)

    # 3rd Requirement (part 1): Add a computed field for the list view display
    scale_display = fields.Char(
        string="Scale",
        compute='_compute_scale_display',
        store=False,  # No need to store this, it's always calculated on the fly
    )

    @api.depends('lower_bound', 'upper_bound')
    def _compute_scale_display(self):
        """Creates the display text like '30% - 40%'."""
        for record in self:
            record.scale_display = f"{record.lower_bound}% - {record.upper_bound}%"

    # # 2nd Requirement (part 2): Add validation to prevent overlapping scales
    # @api.constrains('lower_bound', 'upper_bound')
    # def _check_scale_overlap(self):
    #     """
    #     Ensures that a scale's bounds are valid and do not overlap with any
    #     other scale from the same company.
    #     """
    #     for record in self:
    #         if record.lower_bound >= record.upper_bound:
    #             raise ValidationError(
    #                 _("The Lower Bound must be strictly smaller than the Upper Bound."))

    #         # Domain to find any other scale that overlaps with the current one.
    #         # An overlap occurs if: another_scale.start <= my.end AND another_scale.end >= my.start
    #         overlapping_scales = self.search([
    #             ('id', '!=', record.id),  # Don't compare the record with itself
    #             # Check only within the same company
    #             ('company_id', '=', record.company_id.id),
    #             # The other scale must start before this one ends
    #             ('lower_bound', '<=', record.upper_bound),
    #             # The other scale must end after this one starts
    #             ('upper_bound', '>=', record.lower_bound),
    #         ])

    #         if overlapping_scales:
    #             # Create a readable list of the conflicting scales
    #             conflicts = ", ".join(overlapping_scales.mapped('name'))
    #             raise ValidationError(
    #                 _("The defined scale (%.2f%% - %.2f%%) overlaps with the following existing scale(s): %s") %
    #                 (record.lower_bound, record.upper_bound, conflicts)
    #             )
