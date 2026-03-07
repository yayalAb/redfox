from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrPerformanceQuestion(models.Model):
    _name = "hr.performance.question"
    _description = "360 Performance Evaluation Question"
    _order = "sequence, id"

    config_id = fields.Many2one(
        "hr.performance.confi",
        string="Configuration",
        required=True,
        ondelete="cascade",
        help="The 360 configuration that owns this question.",
    )
    sequence = fields.Integer(string="Sequence", default=10)
    display_type = fields.Selection(
        [
            ("line_section", "Section"),
            ("line_note", "Note"),
            ("question", "Question"),
        ],
        default="question",
        required=True,
        help="Section for grouping questions, Note for additional info, or Question for actual questions.",
    )
    name = fields.Char(
        string="Question / Section Name",
        required=True,
        help="Question used during the 360 evaluation, or section name for grouping.",
    )
    description = fields.Text(
        string="Guidance",
        help="Additional context or guidance for answering the question.",
    )
    section_weight = fields.Float(
        string="Section Weight (%)",
        digits="Product Unit of Measure",
        default=0.0,
        help="Weight/percentage of this section in the overall evaluation (only for sections).",
    )
    
    @api.onchange('display_type')
    def _onchange_display_type(self):
        """Clear section weight when not a section"""
        if self.display_type != 'line_section':
            self.section_weight = 0.0
    
    @api.constrains('display_type', 'section_weight')
    def _check_weight_only_for_sections(self):
        """Ensure weight is only set for sections"""
        for record in self:
            if record.display_type != 'line_section' and record.section_weight != 0:
                raise ValidationError(_("Section weight can only be set for sections, not for questions or notes."))

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('default_display_type'):
            res['display_type'] = self.env.context.get('default_display_type')
        return res

    def _valid_field_parameter(self, field, name):
        # Allow 'required' parameter for name field
        return name == 'required' or super()._valid_field_parameter(field, name)
    
    @api.constrains('display_type', 'name')
    def _check_section_has_name(self):
        for record in self:
            if record.display_type in ('line_section', 'line_note') and not record.name:
                raise ValidationError(_("Section/Note must have a name."))
            if record.display_type == 'question' and not record.name:
                raise ValidationError(_("Question must have a name."))

