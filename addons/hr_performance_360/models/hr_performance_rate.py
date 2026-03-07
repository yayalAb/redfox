from odoo import fields, models


class HrPerformanceRate(models.Model):
    _name = "hr.performance.rate"
    _description = "360 Performance Evaluation Rate"
    _order = "rate_id, category"

    rate_id = fields.Many2one(
        "hr.performance.confi",
        string="Job",
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
    rate = fields.Float(
        string="Rate",
        digits="Product Unit of Measure",
        help="Numeric rating assigned for the evaluator type.",
    )
    note = fields.Char(
        string="Notes",
        help="Provide contextual notes that clarify the evaluator expectation or benchmark.",
    )


