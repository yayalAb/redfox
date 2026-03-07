from odoo import api, fields, models


class HrPerformanceEmployee(models.Model):
    _inherit = "hr.employee"
    _order = "name"

    evaluation_template_id = fields.Many2one(
        "hr.performance.confi",
        string="Evaluation Template",
        compute="_compute_evaluation_template_id",
        help="Evaluation configuration template based on employee's job position.",
    )
    evaluation_type = fields.Selection(
        [
            ("self", "Self"),
            ("peer", "Peer"),
            ("subordinate", "Subordinate"),
            ("supervisor", "Supervisor"),
        ],
        string="Evaluation Type",
        compute="_compute_evaluation_type",
        store=False,
        help="Type of evaluation based on relationship between logged-in user and employee.",
    )

    is_evaluated = fields.Boolean(
        string="Is Evaluated",
        compute="_compute_is_evaluated",
        store=False,
        help="True if the current logged-in user has already evaluated this employee.",
    )

    def action_open_employee_evaluations(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)],
            limit=1
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Evaluations',
            'res_model': 'hr.employee',
            'view_mode': 'list',
            'view_id': self.env.ref(
                'hr_performance_360.hr_performance_employee_list_view'
            ).id,
            'context': {
                'search_default_active': 1,
                'evaluation_view': True,
                'child_ids': employee.child_ids.ids,        # ✅ REQUIRED
                'peer_job_ids': employee.job_id.peer_job_ids.ids,  # ✅ REQUIRED
            },
            'domain': [
                '|', '|', '|', '|',
                ('user_id', '=', self.env.uid),
                ('id', '=', employee.parent_id.id),
                ('id', 'in', employee.child_ids.ids),
                ('job_id', '=', employee.job_id.id),
                ('job_id', 'in', employee.job_id.peer_job_ids.ids),
            ],
        }

    @api.depends("job_id")
    def _compute_evaluation_template_id(self):
        """Compute evaluation template based on employee's job position."""
        for employee in self:
            if employee.job_id:
                # Search for configuration that contains this job position in job_ids
                config = self.env["hr.performance.confi"].search([
                    ("job_ids", "in", [employee.job_id.id])
                ], limit=1, order="id")
                employee.evaluation_template_id = config.id if config else False
            else:
                employee.evaluation_template_id = False

    def _compute_evaluation_type(self):
        """Compute evaluation type based on relationship between logged-in user and employee."""
        current_user_employee = self.env.user.employee_id
        if not current_user_employee:
            # If logged-in user has no associated employee, no evaluation type
            for employee in self:
                employee.evaluation_type = False
            return

        for employee in self:
            eval_type = False
            # 1. Self: logged-in user is evaluating themselves
            if current_user_employee.id == employee.id:
                eval_type = "self"
            # 2. Supervisor: logged-in user is the manager of the employee being evaluated
            elif employee.parent_id and employee.parent_id.id == current_user_employee.id:
                eval_type = "supervisor"

            # 3. Subordinate: logged-in user's manager is the employee being evaluated
            elif current_user_employee.parent_id and current_user_employee.parent_id.id == employee.id:
                eval_type = "subordinate"

            # 4. Peer: logged-in user and employee have peer job positions
            elif current_user_employee.job_id and employee.job_id:
                # Check if logged-in user's job is in employee's job peer list
                if current_user_employee.job_id.id in employee.job_id.peer_job_ids.ids:
                    eval_type = "peer"
                # Check if employee's job is in logged-in user's job peer list
                elif employee.job_id.id in current_user_employee.job_id.peer_job_ids.ids:
                    eval_type = "peer"
                # Also check if they have the same job (could be considered peer)
                elif current_user_employee.job_id.id == employee.job_id.id:
                    eval_type = "peer"

            employee.evaluation_type = eval_type

    def _compute_is_evaluated(self):
        """Check if the current logged-in user has already evaluated this employee."""
        current_user_employee = self.env.user.employee_id
        if not current_user_employee:
            for employee in self:
                employee.is_evaluated = False
            return

        # Get all evaluation types this user could evaluate this employee as
        for employee in self:
            # Compute evaluation type for this employee
            employee._compute_evaluation_type()
            eval_type = employee.evaluation_type

            if not eval_type:
                employee.is_evaluated = False
                continue

            # Check if there's already an evaluation for this employee by this evaluator with this type
            existing_evaluation = self.env["hr.performance.evaluation"].search([
                ("employee_id", "=", employee.id),
                ("evaluator_id", "=", current_user_employee.id),
                ("evaluator_category", "=", eval_type),
            ], limit=1)

            employee.is_evaluated = bool(existing_evaluation)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """Override search_read to filter employees based on evaluation relationships."""
        # If this is the employee evaluations list, filter to show only evaluatable employees
        if self.env.context.get('evaluation_view'):
            current_user_employee = self.env.user.employee_id
            if current_user_employee:
                employee_ids = [current_user_employee.id]

                # Supervisor: direct subordinates
                if current_user_employee.child_ids:
                    employee_ids.extend(current_user_employee.child_ids.ids)

                # Subordinate: manager
                if current_user_employee.parent_id:
                    employee_ids.append(current_user_employee.parent_id.id)

                # Peer: employees with peer job positions
                if current_user_employee.job_id:
                    # Get employees with peer jobs
                    if current_user_employee.job_id.peer_job_ids:
                        peer_employees = self.env['hr.employee'].search([
                            ('job_id', 'in',
                             current_user_employee.job_id.peer_job_ids.ids)
                        ])
                        employee_ids.extend(peer_employees.ids)

                    # Get employees whose job has current user's job as peer
                    jobs_with_peer = self.env['hr.job'].search([
                        ('peer_job_ids', 'in', [
                         current_user_employee.job_id.id])
                    ])
                    if jobs_with_peer:
                        peer_employees2 = self.env['hr.employee'].search([
                            ('job_id', 'in', jobs_with_peer.ids)
                        ])
                        employee_ids.extend(peer_employees2.ids)

                    # Same job position
                    same_job = self.env['hr.employee'].search([
                        ('job_id', '=', current_user_employee.job_id.id)
                    ])
                    employee_ids.extend(same_job.ids)

                # Add domain to filter by evaluatable employees
                employee_ids = list(set(employee_ids))
                domain = domain or []
                domain.append(('id', 'in', employee_ids))

        result = super().search_read(domain=domain, fields=fields,
                                     offset=offset, limit=limit, order=order)

        # Compute is_evaluated for the results if evaluation_view context is set
        if self.env.context.get('evaluation_view') and result:
            employee_ids = [r['id'] for r in result]
            employees = self.browse(employee_ids)
            employees._compute_evaluation_type()
            employees._compute_is_evaluated()

            # Add is_evaluated to result records
            evaluated_map = {emp.id: emp.is_evaluated for emp in employees}
            for record in result:
                record['is_evaluated'] = evaluated_map.get(record['id'], False)

        return result

    def action_open_performance_evaluation(self):
        self.ensure_one()
        # Ensure evaluation_type is computed for this employee (compute for single record)
        current_user_employee = self.env.user.employee_id
        eval_type = False

        if current_user_employee:
            # 1. Self: logged-in user is evaluating themselves
            if current_user_employee.id == self.id:
                eval_type = "self"
            # 2. Supervisor: logged-in user is the manager of the employee being evaluated
            elif self.parent_id and self.parent_id.id == current_user_employee.id:
                eval_type = "supervisor"
            # 3. Subordinate: logged-in user's manager is the employee being evaluated
            elif current_user_employee.parent_id and current_user_employee.parent_id.id == self.id:
                eval_type = "subordinate"
            # 4. Peer: logged-in user and employee have peer job positions
            elif current_user_employee.job_id and self.job_id:
                # Check if logged-in user's job is in employee's job peer list
                if current_user_employee.job_id.id in (self.job_id.peer_job_ids.ids if self.job_id.peer_job_ids else []):
                    eval_type = "peer"
                # Check if employee's job is in logged-in user's job peer list
                elif self.job_id.id in (current_user_employee.job_id.peer_job_ids.ids if current_user_employee.job_id.peer_job_ids else []):
                    eval_type = "peer"
                # Also check if they have the same job (could be considered peer)
                elif current_user_employee.job_id.id == self.job_id.id:
                    eval_type = "peer"

        # Ensure evaluation_template_id is computed
        if not self.evaluation_template_id and self.job_id:
            config = self.env["hr.performance.confi"].search([
                ("job_ids", "in", [self.job_id.id])
            ], limit=1, order="id")
            if config:
                self.evaluation_template_id = config.id

        view = self.env.ref(
            "hr_performance_360.hr_evaluation_direct_form_view")
        return {
            "name": "Employee Evaluation",
            "type": "ir.actions.act_window",
            "res_model": "hr.performance.evaluation",
            "view_mode": "form",
            "view_id": view.id,
            "target": "current",
            "context": dict(
                self.env.context,
                default_employee_id=self.id,
                default_evaluator_category=eval_type,
                default_config_id=self.evaluation_template_id.id if self.evaluation_template_id else False,
                default_evaluator_id=current_user_employee.id if current_user_employee else False,
                form_view_initial_mode="edit",
                use_custom_widget=True,  # Flag to indicate we want the custom widget
            ),
        }
