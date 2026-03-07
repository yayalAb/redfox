from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrPerformanceConfi(models.Model):
    _name = "hr.performance.confi"
    _description = "360 Performance Evaluation configuration "
    name = fields.Char(
        string="Name",
        required=True,
        help="Name of the 360 Performance Evaluation Configuration.",
    )

    job_ids = fields.Many2many(
        "hr.job",
        string="Positions",
        required=True,
        ondelete="cascade",
        help="Job position that owns this evaluator rate row.",
    )
    category = fields.Selection(
        [
            ("self", "Self"),
            ("peer", "Peer"),
            ("subordinate", "Subordinate"),
            ("supervisor", "Supervisor"),
        ],
        string="Evaluator Type",
        required=True,
        default="self",
        help="Defines whether the score is coming from self, peer, subordinate, or supervisor.",
    )

    note = fields.Char(
        string="Notes",
        help="Provide contextual notes that clarify the evaluator expectation or benchmark.",
    )

    rate_ids = fields.One2many(
        "hr.performance.rate",
        "rate_id",
        string="360 Evaluation Rates",
        help="Rates assigned for different evaluator types that can give feedback to this role.",
    )

    question_ids = fields.One2many(
        "hr.performance.question",
        "config_id",
        string="Question List",
        help="Questions evaluators answer when assessing this role.",
        copy=True,
    )

    def action_add_section(self):
        """Create a new section directly"""
        self.ensure_one()
        # Get the max sequence to add at the end
        max_sequence = max(self.question_ids.mapped("sequence") or [0])
        self.env["hr.performance.question"].create({
            "config_id": self.id,
            "display_type": "line_section",
            "name": "New Section",
            "sequence": max_sequence + 10,
        })
        return False

    def action_add_question(self):
        """Create a new question directly"""
        self.ensure_one()
        # Get the max sequence to add at the end
        max_sequence = max(self.question_ids.mapped("sequence") or [0])
        self.env["hr.performance.question"].create({
            "config_id": self.id,
            "display_type": "question",
            "name": "New Question",
            "sequence": max_sequence + 10,
        })
        return False

    def action_add_note(self):
        """Create a new note directly"""
        self.ensure_one()
        # Get the max sequence to add at the end
        max_sequence = max(self.question_ids.mapped("sequence") or [0])
        self.env["hr.performance.question"].create({
            "config_id": self.id,
            "display_type": "line_note",
            "name": "New Note",
            "sequence": max_sequence + 10,
        })
        return False

    @api.constrains("rate_ids")
    def _check_rate_sum(self):
        for record in self:
            if not record.rate_ids:
                raise ValidationError(
                    "At least one evaluator rate must be defined per configuration."
                )
            total = sum(rate or 0.0 for rate in record.rate_ids.mapped("rate"))
            if abs(total - 100.0) > 0.0001:
                raise ValidationError(
                    "The total of all evaluator rates must equal 100% per configuration."
                )
            categories = record.rate_ids.mapped("category")
            if len(categories) != len(set(categories)):
                raise ValidationError(
                    "Each evaluator category must be unique per configuration."
                )
