from odoo import api, fields, models
from odoo.exceptions import UserError


class HrPerformanceEvaluation(models.Model):
    _name = "hr.performance.evaluation"
    _description = "Employee 360 Evaluation"
    _order = "evaluation_date desc, id desc"

    name = fields.Char(
        string="Evaluation Reference",
        compute="_compute_name",
        store=True,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        help="Employee who is being evaluated.",
    )
    config_id = fields.Many2one(
        "hr.performance.confi",
        string="Configuration",
        required=True,
        help="360 configuration that defines rate targets and questions.",
    )
    evaluator_id = fields.Many2one(
        "hr.employee",
        string="Evaluator",
        default=lambda self: self.env.user.employee_id,
        help="Person who performed this evaluation.",
    )
    evaluator_category = fields.Selection(
        [
            ("self", "Self"),
            ("peer", "Peer"),
            ("subordinate", "Subordinate"),
            ("supervisor", "Supervisor"),
        ],
        string="Evaluator Type",
        help="Type of evaluator based on relationship to employee.",
    )
    evaluation_date = fields.Date(
        string="Evaluation Date",
        default=fields.Date.context_today,
        required=True,
    )
    total_score = fields.Float(
        string="Total Score",
        digits="Product Unit of Measure",
        compute="_compute_total_score",
        store=True,
    )
    line_ids = fields.One2many(
        "hr.performance.evaluation.line",
        "evaluation_id",
        string="Question Responses",
        copy=True,
    )
    note = fields.Text(string="Notes")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_review", "In Review"),
            ("validated", "Validated"),
        ],
        string="Status",
        default="draft",
    )
    # Temporary field for the widget
    question_data = fields.Text(string="Question Data", invisible=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("default_employee_id"):
            employee_id = self.env.context.get("default_employee_id")
            employee = self.env["hr.employee"].browse(employee_id)
            
            # Use evaluation_template_id from employee if available
            config_id = self.env.context.get("default_config_id")
            if not config_id and employee.evaluation_template_id:
                config_id = employee.evaluation_template_id.id
            elif not config_id:
                # Fallback: Get the first configuration
                config = self.env["hr.performance.confi"].search([], limit=1, order="id")
                config_id = config.id if config else False
            
            if config_id:
                res["config_id"] = config_id
                res["employee_id"] = employee_id
                res["evaluation_date"] = fields.Date.context_today(self)
                
                # Set evaluator_category from context or employee's evaluation_type
                evaluator_category = self.env.context.get("default_evaluator_category")
                if not evaluator_category and employee:
                    # Recompute evaluation_type for the employee
                    employee._compute_evaluation_type()
                    evaluator_category = employee.evaluation_type
                if evaluator_category:
                    res["evaluator_category"] = evaluator_category
                
                # Set evaluator_id from context or current user's employee
                evaluator_id = self.env.context.get("default_evaluator_id")
                if not evaluator_id and self.env.user.employee_id:
                    res["evaluator_id"] = self.env.user.employee_id.id
                elif evaluator_id:
                    res["evaluator_id"] = evaluator_id
        return res

    @api.depends("employee_id", "evaluation_date")
    def _compute_name(self):
        for record in self:
            if record.employee_id and record.evaluation_date:
                record.name = f"{record.employee_id.name} - {record.evaluation_date}"
            else:
                record.name = "New Evaluation"

    @api.depends("line_ids.section_average_rating", "line_ids.section_name", "line_ids.display_section_header")
    def _compute_total_score(self):
        """Compute total score as the sum of all section ratings only (not question ratings)."""
        for record in self:
            # Only get section ratings - section_average_rating is only set on section header rows
            # Use display_section_header to identify section rows (not question rows)
            section_ratings = {}
            for line in record.line_ids:
                # Only include lines that represent sections (have display_section_header set)
                if line.display_section_header and line.section_average_rating:
                    # Use section_name as key to ensure each section is counted only once
                    section_key = line.section_name
                    if section_key and section_key not in section_ratings:
                        section_ratings[section_key] = line.section_average_rating
            
            # Sum only the section ratings (not question ratings)
            record.total_score = sum(section_ratings.values())

    def action_save_evaluation_from_widget(self):
        """Called from the widget to save evaluation with question data"""
        self.ensure_one()
        # The widget will have already created/updated the line_ids
        # This method can be used for any post-processing if needed
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.performance.evaluation",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    _sql_constraints = [
        (
            "unique_employee_evaluator",
            "unique(employee_id, evaluator_id)",
            "Each evaluator can only evaluate an employee once. An evaluation already exists for this employee and evaluator combination.",
        ),
    ]


class HrPerformanceEvaluationLine(models.Model):
    _name = "hr.performance.evaluation.line"
    _description = "360 Evaluation Question Answer"
    _order = "evaluation_id, section_sequence, question_sequence"

    evaluation_id = fields.Many2one(
        "hr.performance.evaluation",
        string="Evaluation",
        required=True,
        ondelete="cascade",
    )
    question_id = fields.Many2one(
        "hr.performance.question",
        string="Question",
        required=True,
        help="Question answered as part of the evaluation.",
    )
    rating = fields.Float(
        string="Rating",
        digits="Product Unit of Measure",
        help="Numeric answer provided for this question.",
    )
    comment = fields.Text(string="Comment")
    
    # Section information fields for grouping
    section_name = fields.Char(
        string="Section",
        compute="_compute_section_info",
        store=True,
        help="Section this question belongs to.",
    )
    section_sequence = fields.Integer(
        string="Section Sequence",
        compute="_compute_section_info",
        store=True,
        help="Sequence of the section for ordering.",
    )
    question_sequence = fields.Integer(
        string="Question Sequence",
        related="question_id.sequence",
        store=True,
        help="Sequence of the question within the section.",
    )
    section_weight = fields.Float(
        string="Section Weight",
        compute="_compute_section_info",
        store=True,
        help="Weight of the section this question belongs to.",
    )
    display_section_header = fields.Char(
        string="Section Header",
        compute="_compute_section_info",
        store=False,
        help="Section name to display as header for this group.",
    )
    criteria_display = fields.Char(
        string="Criteria Display",
        compute="_compute_criteria_display",
        store=False,
        help="Combined display field showing section header or question name.",
    )
    rating_display = fields.Float(
        string="Rating Display",
        compute="_compute_rating_display",
        inverse="_inverse_rating_display",
        store=False,
        digits="Product Unit of Measure",
        help="Shows section average rating for section headers, otherwise question rating.",
    )
    section_average_rating = fields.Float(
        string="Section Average Rating",
        compute="_compute_section_info",
        store=False,
        digits="Product Unit of Measure",
        help="Average rating of all questions in this section.",
    )

    @api.depends("display_section_header", "question_id", "question_id.name")
    def _compute_criteria_display(self):
        """Compute criteria display: show section header if available, otherwise question name."""
        for line in self:
            if line.display_section_header:
                line.criteria_display = line.display_section_header
            elif line.question_id:
                line.criteria_display = line.question_id.name
            else:
                line.criteria_display = ""
    
    @api.depends("display_section_header", "section_average_rating", "rating", "evaluation_id.line_ids.rating")
    def _compute_rating_display(self):
        """Compute rating display: show section average for section headers, otherwise question rating."""
        for line in self:
            if line.display_section_header and line.section_average_rating:
                line.rating_display = line.section_average_rating
            else:
                line.rating_display = line.rating or 0.0
    
    def _inverse_rating_display(self):
        """When rating_display is edited, update the underlying rating field."""
        for line in self:
            if not line.display_section_header:
                # Only update rating if it's not a section header
                line.rating = line.rating_display
    
    @api.onchange("criteria_display")
    def _onchange_criteria_display(self):
        """Handle manual editing of criteria_display if needed."""
        # This is primarily a display field, but we keep this for potential future use
        pass

    @api.depends("question_id", "evaluation_id.config_id", "rating", "evaluation_id.line_ids.rating")
    def _compute_section_info(self):
        """Compute section information for each evaluation line based on configuration."""
        # Process all lines together to avoid recursive dependency
        lines_to_process = self.filtered(lambda l: l.question_id and l.evaluation_id.config_id)
        
        # Group by evaluation to process efficiently
        eval_groups = {}
        for line in lines_to_process:
            eval_id = line.evaluation_id.id
            if eval_id not in eval_groups:
                eval_groups[eval_id] = []
            eval_groups[eval_id].append(line)
        
        for eval_id, lines in eval_groups.items():
            if not lines:
                continue
                
            config = lines[0].evaluation_id.config_id
            # Get all questions/sections from the config ordered by sequence
            all_items = self.env["hr.performance.question"].search([
                ("config_id", "=", config.id)
            ], order="sequence, id")
            
            # Build a mapping of question_id to section
            question_to_section = {}
            current_section = None
            current_section_seq = 0
            
            for item in all_items:
                if item.display_type == "line_section":
                    current_section = item
                    current_section_seq = item.sequence
                elif item.display_type == "question" or not item.display_type:
                    if current_section:
                        question_to_section[item.id] = {
                            "section": current_section,
                            "sequence": current_section_seq,
                        }
                    else:
                        question_to_section[item.id] = {
                            "section": None,
                            "sequence": 0,
                        }
            
            # Assign section info to lines
            section_first_question = {}  # Track first question of each section
            for line in sorted(lines, key=lambda l: (
                question_to_section.get(l.question_id.id, {}).get("sequence", 0),
                l.question_id.sequence if l.question_id else 0
            )):
                section_info = question_to_section.get(line.question_id.id, {})
                section = section_info.get("section")
                
                if section:
                    line.section_name = section.name
                    line.section_sequence = section_info.get("sequence", 0)
                    line.section_weight = section.section_weight or 0.0
                    
                    # Track if this is the first question in this section
                    section_key = (line.section_name, line.evaluation_id.id)
                    if section_key not in section_first_question:
                        section_first_question[section_key] = line.id
                else:
                    line.section_name = False
                    line.section_sequence = 0
                    line.section_weight = 0.0
            
            # Calculate section average ratings - need all lines for the evaluation
            evaluation = lines[0].evaluation_id
            all_eval_lines = evaluation.line_ids.filtered(lambda l: l.question_id)
            
            # Count questions per section (including unrated ones)
            section_question_counts = {}  # {section_key: count}
            section_rating_sums = {}  # {section_key: sum_of_ratings}
            
            for line in all_eval_lines:
                if line.question_id:
                    # Determine section for this line based on question_id
                    section_info = question_to_section.get(line.question_id.id, {})
                    section = section_info.get("section")
                    if section:
                        section_key = (section.name, line.evaluation_id.id)
                        # Count all questions in section
                        if section_key not in section_question_counts:
                            section_question_counts[section_key] = 0
                            section_rating_sums[section_key] = 0.0
                        section_question_counts[section_key] += 1
                        # Add rating (0 if not rated)
                        section_rating_sums[section_key] += (line.rating or 0.0)
            
            # Set display_section_header and section_average_rating for first question of each section
            for line in lines:
                if line.section_name:
                    section_key = (line.section_name, line.evaluation_id.id)
                    if section_first_question.get(section_key) == line.id:
                        # Calculate average rating for this section: sum / count
                        question_count = section_question_counts.get(section_key, 0)
                        rating_sum = section_rating_sums.get(section_key, 0.0)
                        if question_count > 0:
                            average_rating = rating_sum / question_count
                            # Calculate weighted rating: (average * weight) / 5 * 100
                            section_weight = line.section_weight or 0.0
                            if section_weight > 0:
                                line.section_average_rating = ((average_rating * section_weight) / 5.0) * 100.0
                            else:
                                line.section_average_rating = average_rating * 100.0
                        else:
                            line.section_average_rating = 0.0
                        
                        # Build section header with weight
                        # Multiply weight by 100 to display as percentage (e.g., 20% instead of 0.2%)
                        weight_display = line.section_weight * 100.0 if line.section_weight else 0.0
                        weight_text = f" ({weight_display:.0f}%)" if line.section_weight else ""
                        line.display_section_header = f"{line.section_name}{weight_text}"
                    else:
                        line.display_section_header = False
                        line.section_average_rating = 0.0
                else:
                    line.display_section_header = False
                    line.section_average_rating = 0.0
        
        # Clear section info for lines without question_id or config_id
        for line in self - lines_to_process:
            line.section_name = False
            line.section_sequence = 0
            line.section_weight = 0.0
            line.display_section_header = False

    @api.constrains("employee_id", "evaluator_id")
    def _check_unique_evaluation(self):
        """Ensure each evaluator can only evaluate an employee once."""
        for record in self:
            if record.employee_id and record.evaluator_id:
                existing = self.search([
                    ("employee_id", "=", record.employee_id.id),
                    ("evaluator_id", "=", record.evaluator_id.id),
                    ("id", "!=", record.id),
                ], limit=1)
                if existing:
                    raise UserError(
                        f"This employee ({record.employee_id.name}) has already been evaluated by "
                        f"{record.evaluator_id.name}. Each evaluator can only evaluate an employee once."
                    )

    _sql_constraints = [
        (
            "unique_question_per_evaluation",
            "unique(evaluation_id, question_id)",
            "Each question can only be scored once per evaluation.",
        ),
    ]
