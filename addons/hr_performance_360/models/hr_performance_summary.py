from odoo import api, fields, models


class HrPerformanceEvaluationSummary(models.Model):
    _name = "hr.performance.evaluation.summary"
    _description = "Employee 360 Evaluation Summary Report"
    _auto = False
    _order = "employee_id, evaluation_date desc"

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        readonly=True,
    )
    employee_name = fields.Char(string="Employee Name", readonly=True)
    evaluation_date = fields.Date(string="Evaluation Date", readonly=True)
    supervisor_score = fields.Float(string="Supervisor", readonly=True, digits="Product Unit of Measure")
    subordinate_score = fields.Float(string="Subordinate", readonly=True, digits="Product Unit of Measure")
    peer_score = fields.Float(string="Peer", readonly=True, digits="Product Unit of Measure")
    self_score = fields.Float(string="Self", readonly=True, digits="Product Unit of Measure")
    total_score = fields.Float(string="Total Score", readonly=True, digits="Product Unit of Measure")
    supervisor_count = fields.Integer(string="Supervisor Count", readonly=True)
    subordinate_count = fields.Integer(string="Subordinate Count", readonly=True)
    peer_count = fields.Integer(string="Peer Count", readonly=True)
    self_count = fields.Integer(string="Self Count", readonly=True)

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW hr_performance_evaluation_summary AS (
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY emp.id) AS id,
                    emp.id AS employee_id,
                    emp.name AS employee_name,
                    COALESCE(MAX(e.evaluation_date), CURRENT_DATE) AS evaluation_date,
                    -- Sum of all supervisor evaluations
                    COALESCE(SUM(CASE WHEN e.evaluator_category = 'supervisor' THEN e.total_score ELSE 0 END), 0) AS supervisor_score,
                    -- Sum of all subordinate evaluations
                    COALESCE(SUM(CASE WHEN e.evaluator_category = 'subordinate' THEN e.total_score ELSE 0 END), 0) AS subordinate_score,
                    -- Sum of all peer evaluations
                    COALESCE(SUM(CASE WHEN e.evaluator_category = 'peer' THEN e.total_score ELSE 0 END), 0) AS peer_score,
                    -- Sum of all self evaluations
                    COALESCE(SUM(CASE WHEN e.evaluator_category = 'self' THEN e.total_score ELSE 0 END), 0) AS self_score,
                    -- Total score (sum of supervisor + subordinate + peer + self)
                    COALESCE(
                        SUM(CASE WHEN e.evaluator_category = 'supervisor' THEN e.total_score ELSE 0 END) +
                        SUM(CASE WHEN e.evaluator_category = 'subordinate' THEN e.total_score ELSE 0 END) +
                        SUM(CASE WHEN e.evaluator_category = 'peer' THEN e.total_score ELSE 0 END) +
                        SUM(CASE WHEN e.evaluator_category = 'self' THEN e.total_score ELSE 0 END),
                        0
                    ) AS total_score,
                    -- Count of evaluations by type
                    COUNT(CASE WHEN e.evaluator_category = 'supervisor' THEN 1 END) AS supervisor_count,
                    COUNT(CASE WHEN e.evaluator_category = 'subordinate' THEN 1 END) AS subordinate_count,
                    COUNT(CASE WHEN e.evaluator_category = 'peer' THEN 1 END) AS peer_count,
                    COUNT(CASE WHEN e.evaluator_category = 'self' THEN 1 END) AS self_count
                FROM hr_employee emp
                LEFT JOIN hr_performance_evaluation e ON emp.id = e.employee_id 
                    AND (e.state IS NULL OR e.state != 'draft')
                WHERE emp.active = True
                GROUP BY emp.id, emp.name
            )
        """)

