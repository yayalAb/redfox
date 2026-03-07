from odoo import api, fields, models


class HrPerformanceEvaluationSummaryDetail(models.Model):
    _name = "hr.performance.evaluation.summary.detail"
    _description = "Employee 360 Evaluation Summary Detail"
    _auto = False
    _order = "employee_id"

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        readonly=True,
        required=True,
    )
    config_id = fields.Many2one(
        "hr.performance.confi",
        string="Evaluation Configuration",
        readonly=True,
    )
    
    # Rates from configuration
    supervisor_rate = fields.Float(
        string="Supervisor Rate (%)",
        readonly=True,
        digits="Product Unit of Measure",
        help="Supervisor rate percentage from evaluation configuration.",
    )
    subordinate_rate = fields.Float(
        string="Subordinate Rate (%)",
        readonly=True,
        digits="Product Unit of Measure",
        help="Subordinate rate percentage from evaluation configuration.",
    )
    peer_rate = fields.Float(
        string="Peer Rate (%)",
        readonly=True,
        digits="Product Unit of Measure",
        help="Peer rate percentage from evaluation configuration.",
    )
    self_rate = fields.Float(
        string="Self Rate (%)",
        readonly=True,
        digits="Product Unit of Measure",
        help="Self rate percentage from evaluation configuration.",
    )
    
    # Results from evaluations (sum of total_score by evaluator_category)
    supervisor_result = fields.Float(
        string="Supervisor Result",
        readonly=True,
        digits="Product Unit of Measure",
        help="Sum of total scores from supervisor evaluations.",
    )
    subordinate_result = fields.Float(
        string="Subordinate Result",
        readonly=True,
        digits="Product Unit of Measure",
        help="Sum of total scores from subordinate evaluations.",
    )
    peer_result = fields.Float(
        string="Peer Result",
        readonly=True,
        digits="Product Unit of Measure",
        help="Sum of total scores from peer evaluations.",
    )
    self_result = fields.Float(
        string="Self Result",
        readonly=True,
        digits="Product Unit of Measure",
        help="Sum of total scores from self evaluations.",
    )
    total_percentage = fields.Float(
        string="Total %",
        readonly=True,
        digits="Product Unit of Measure",
        help="Sum of all section weights (percentages) from the evaluation configuration.",
    )
    supervisor_weighted = fields.Float(
        string="Supervisor Weighted",
        readonly=True,
        digits="Product Unit of Measure",
        help="Supervisor result weighted by supervisor rate: (supervisor_result * supervisor_rate) / 100",
    )
    subordinate_weighted = fields.Float(
        string="Subordinate Weighted",
        readonly=True,
        digits="Product Unit of Measure",
        help="Subordinate result weighted by subordinate rate: (subordinate_result * subordinate_rate) / 100",
    )
    peer_weighted = fields.Float(
        string="Peer Weighted",
        readonly=True,
        digits="Product Unit of Measure",
        help="Peer result weighted by peer rate: (peer_result * peer_rate) / 100",
    )
    self_weighted = fields.Float(
        string="Self Weighted",
        readonly=True,
        digits="Product Unit of Measure",
        help="Self result weighted by self rate: (self_result * self_rate) / 100",
    )
    total_weighted = fields.Float(
        string="Total Weighted",
        readonly=True,
        digits="Product Unit of Measure",
        help="Sum of all weighted scores: supervisor_weighted + subordinate_weighted + peer_weighted + self_weighted",
    )

    def init(self):
        """Initialize the database view for evaluation summary detail.
        
        Gets evaluation results from: hr.performance.evaluation (Employee Evaluation Results)
        Gets configuration rates from: hr.performance.confi (360 Performance Evaluation Configuration)
        
        Shows immediate results for each employee that has at least one evaluation.
        """
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW hr_performance_evaluation_summary_detail AS (
                -- Step 1: Get all employees that have at least one evaluation from Employee Evaluation Results
                -- Include all evaluations including draft ones
                WITH employees_with_evaluations AS (
                    SELECT DISTINCT 
                        e.employee_id,
                        e.config_id
                    FROM hr_performance_evaluation e
                    INNER JOIN hr_employee emp ON emp.id = e.employee_id
                    WHERE emp.active = True
                ),
                -- Step 2: Get configuration rates aggregated by config
                config_rates AS (
                    SELECT 
                        r.rate_id AS config_id,
                        MAX(CASE WHEN r.category = 'supervisor' THEN r.rate ELSE NULL END) AS supervisor_rate,
                        MAX(CASE WHEN r.category = 'subordinate' THEN r.rate ELSE NULL END) AS subordinate_rate,
                        MAX(CASE WHEN r.category = 'peer' THEN r.rate ELSE NULL END) AS peer_rate,
                        MAX(CASE WHEN r.category = 'self' THEN r.rate ELSE NULL END) AS self_rate
                    FROM hr_performance_rate r
                    GROUP BY r.rate_id
                ),
                -- Step 2b: Get total percentage (sum of section weights) by config
                config_total_percentage AS (
                    SELECT 
                        q.config_id,
                        COALESCE(SUM(q.section_weight), 0) AS total_percentage
                    FROM hr_performance_question q
                    WHERE q.display_type = 'line_section'
                    GROUP BY q.config_id
                ),
                -- Step 3: Get evaluation results aggregated by employee, config, and evaluator_category
                -- Calculate average (sum divided by count) for each evaluator category
                evaluation_results AS (
                    SELECT 
                        e.employee_id,
                        e.config_id,
                        CASE 
                            WHEN COUNT(CASE WHEN e.evaluator_category = 'supervisor' THEN 1 END) > 0 
                            THEN SUM(CASE WHEN e.evaluator_category = 'supervisor' THEN e.total_score ELSE 0 END)::numeric / 
                                 COUNT(CASE WHEN e.evaluator_category = 'supervisor' THEN 1 END)
                            ELSE 0 
                        END AS supervisor_result,
                        CASE 
                            WHEN COUNT(CASE WHEN e.evaluator_category = 'subordinate' THEN 1 END) > 0 
                            THEN SUM(CASE WHEN e.evaluator_category = 'subordinate' THEN e.total_score ELSE 0 END)::numeric / 
                                 COUNT(CASE WHEN e.evaluator_category = 'subordinate' THEN 1 END)
                            ELSE 0 
                        END AS subordinate_result,
                        CASE 
                            WHEN COUNT(CASE WHEN e.evaluator_category = 'peer' THEN 1 END) > 0 
                            THEN SUM(CASE WHEN e.evaluator_category = 'peer' THEN e.total_score ELSE 0 END)::numeric / 
                                 COUNT(CASE WHEN e.evaluator_category = 'peer' THEN 1 END)
                            ELSE 0 
                        END AS peer_result,
                        CASE 
                            WHEN COUNT(CASE WHEN e.evaluator_category = 'self' THEN 1 END) > 0 
                            THEN SUM(CASE WHEN e.evaluator_category = 'self' THEN e.total_score ELSE 0 END)::numeric / 
                                 COUNT(CASE WHEN e.evaluator_category = 'self' THEN 1 END)
                            ELSE 0 
                        END AS self_result
                    FROM hr_performance_evaluation e
                    GROUP BY e.employee_id, e.config_id
                )
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY ewe.employee_id, ewe.config_id) AS id,
                    ewe.employee_id,
                    ewe.config_id,
                    -- Get rates from configuration
                    COALESCE(cr.supervisor_rate, 0) AS supervisor_rate,
                    COALESCE(cr.subordinate_rate, 0) AS subordinate_rate,
                    COALESCE(cr.peer_rate, 0) AS peer_rate,
                    COALESCE(cr.self_rate, 0) AS self_rate,
                    -- Get results from evaluations
                    COALESCE(er.supervisor_result, 0) AS supervisor_result,
                    COALESCE(er.subordinate_result, 0) AS subordinate_result,
                    COALESCE(er.peer_result, 0) AS peer_result,
                    COALESCE(er.self_result, 0) AS self_result,
                    -- Get total percentage (sum of section weights)
                    COALESCE(ctp.total_percentage, 0) AS total_percentage,
                    -- Calculate weighted scores: (result * rate) / 100
                    (COALESCE(er.supervisor_result, 0) * COALESCE(cr.supervisor_rate, 0) / 100.0) AS supervisor_weighted,
                    (COALESCE(er.subordinate_result, 0) * COALESCE(cr.subordinate_rate, 0) / 100.0) AS subordinate_weighted,
                    (COALESCE(er.peer_result, 0) * COALESCE(cr.peer_rate, 0) / 100.0) AS peer_weighted,
                    (COALESCE(er.self_result, 0) * COALESCE(cr.self_rate, 0) / 100.0) AS self_weighted,
                    -- Calculate total weighted (sum of all 4 weighted scores)
                    ((COALESCE(er.supervisor_result, 0) * COALESCE(cr.supervisor_rate, 0) / 100.0) +
                     (COALESCE(er.subordinate_result, 0) * COALESCE(cr.subordinate_rate, 0) / 100.0) +
                     (COALESCE(er.peer_result, 0) * COALESCE(cr.peer_rate, 0) / 100.0) +
                     (COALESCE(er.self_result, 0) * COALESCE(cr.self_rate, 0) / 100.0)) AS total_weighted
                FROM employees_with_evaluations ewe
                LEFT JOIN config_rates cr ON cr.config_id = ewe.config_id
                LEFT JOIN config_total_percentage ctp ON ctp.config_id = ewe.config_id
                LEFT JOIN evaluation_results er ON er.employee_id = ewe.employee_id 
                    AND er.config_id = ewe.config_id
            )
        """)
