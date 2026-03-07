from odoo import fields, models


class HrJob(models.Model):
    _inherit = "hr.job"

    peer_job_ids = fields.Many2many(
        "hr.job",
        "hr_job_peer_rel",
        "job_id",
        "peer_job_id",
        string="Peer Positions",
        help="List of peer positions that are part of this job's 360 evaluation set.",
    )


