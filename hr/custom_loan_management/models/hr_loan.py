from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import math


class HrLoan(models.Model):
    _inherit = 'hr.loan'

    # --- REQUIREMENT 1: FIELDS ---
    # The new field for the user to input the desired payment amount.
    installment_amount = fields.Float(
        string="Amount Per Installment",
        tracking=True,
        help="The amount the employee will pay per installment. This will be used to calculate the number of installments."
    )

    # We are not changing the original 'installment' field in Python,
    # as its value will now be set by our new logic. We will make it
    # readonly in the XML view.

    # --- REQUIREMENT 2: FIELDS ---
    is_employee_manager = fields.Boolean(
        string="Is Manager?",
        compute='_compute_is_manager',
        help="Checked if the employee has direct reports."
    )
    manager_loan_type = fields.Selection(
        [
            ('emergency', 'Emergency Loan'),
            ('fixed_asset', 'Fixed Asset Loan'),
        ],
        string="Manager Loan Type",
        tracking=True
    )

    has_grace_period = fields.Boolean(
        string="Add Grace Period",
        tracking=True,
        help="Check this box to define a period where no installments will be scheduled."
    )
    grace_period_start_date = fields.Date(
        string="Grace Period Start Date",
        tracking=True
    )
    grace_period_end_date = fields.Date(
        string="Grace Period End Date",
        tracking=True
    )

    is_special_loan = fields.Boolean(
        string="Special Loan (Bypass Policy)",
        tracking=True,
        default=False,
        help="If checked, the standard loan amount policies will be ignored for this request. This should only be used in exceptional cases and requires manager approval."
    )

    adjust_installment_amount = fields.Boolean(
        string="Adjust Amount Per Installment",
        default=False,
        tracking=True,
        help="Check this box to calculate the schedule based on a fixed payment amount. Uncheck to calculate based on a fixed number of installments."
    )
    sequence_no = fields.Integer(
        string='S.No.',
        compute='_compute_sequence_no'
    )
    pay_in_cash = fields.Boolean(
        string="Pay in Cash",
        default=False,
        help="If checked, this loan will not be deducted from the payslip."
    )

    @api.depends('name')
    def _compute_sequence_no(self):
        for index, record in enumerate(self.sorted(key=lambda r: r.employee_id.name), start=1):
            record.sequence_no = index

    @api.depends('employee_id')
    def _compute_is_manager(self):
        """A simple check to see if an employee is a manager."""
        for loan in self:
            loan.is_employee_manager = bool(
                loan.employee_id and loan.employee_id.child_ids)

    def _recompute_installments(self):
        """
        Master method to re-compute installments based on the user's chosen method.
        It respects paid installments and handles grace periods.
        """
        for loan in self:
            # --- PRE-CHECKS ---
            if loan.loan_amount <= 0 or not loan.payment_date:
                continue
            if loan.has_grace_period and (not loan.grace_period_start_date or not loan.grace_period_end_date):
                continue

            # --- INITIAL CALCULATION ---
            paid_lines = loan.loan_line_ids.filtered(lambda line: line.paid)
            paid_amount = sum(paid_lines.mapped('amount'))
            balance_amount = loan.loan_amount - paid_amount

            # --- CLEAR UNPAID LINES ---
            unpaid_lines = loan.loan_line_ids.filtered(
                lambda line: not line.paid)
            if unpaid_lines:
                unpaid_lines.unlink()

            # --- DUAL LOGIC FOR INSTALLMENT CALCULATION ---
            new_lines_vals = []

            # Logic Branch 1: Calculate based on a fixed NUMBER of installments
            if not loan.adjust_installment_amount:
                if loan.installment <= len(paid_lines):
                    # User reduced the number of installments to something already paid. Do nothing.
                    continue

                remaining_installments = loan.installment - len(paid_lines)
                if remaining_installments <= 0:
                    continue  # Avoid division by zero

                amount_per_installment = balance_amount / remaining_installments

                # We will create exactly 'remaining_installments' lines.
                for i in range(remaining_installments):
                    # For the last installment, assign the remaining balance to avoid float errors
                    amount_to_pay = amount_per_installment if i < remaining_installments - \
                        1 else balance_amount
                    new_lines_vals.append({
                        'amount': amount_to_pay,
                    })
                    balance_amount -= amount_to_pay  # Decrement balance for the last line calculation

            # Logic Branch 2: Calculate based on a fixed AMOUNT per installment
            else:
                if loan.installment_amount <= 0:
                    continue  # Cannot calculate if amount is zero

                temp_balance = balance_amount
                while temp_balance > 0.01:
                    amount_to_pay = min(loan.installment_amount, temp_balance)
                    new_lines_vals.append({
                        'amount': amount_to_pay,
                    })
                    temp_balance -= amount_to_pay

            # --- DATE SCHEDULING & FINAL WRITE (Common for both logics) ---
            if not new_lines_vals:
                continue

            next_installment_date = loan.payment_date
            if paid_lines:
                last_paid_date = max(paid_lines.mapped('date'))
                if next_installment_date <= last_paid_date:
                    next_installment_date = last_paid_date + \
                        relativedelta(months=1)

            # Add the dates to our calculated lines
            for vals in new_lines_vals:
                if loan.has_grace_period and \
                   loan.grace_period_start_date <= next_installment_date <= loan.grace_period_end_date:
                    next_installment_date = loan.grace_period_end_date + \
                        relativedelta(months=1)

                vals['date'] = next_installment_date
                vals['employee_id'] = loan.employee_id.id
                next_installment_date += relativedelta(months=1)

            if new_lines_vals:
                loan.with_context(bypass_write_trigger=True).write({
                    'loan_line_ids': [(0, 0, vals) for vals in new_lines_vals],
                    'installment': len(paid_lines) + len(new_lines_vals)
                })

    # You also need to add 'has_grace_period' and its date fields to the write trigger
    def write(self, vals):
        """ On save/write, call the original write, then re-compute if necessary. """
        if self.env.context.get('bypass_write_trigger'):
            return super(HrLoan, self).write(vals)

        res = super(HrLoan, self).write(vals)
        if 'loan_amount' in vals or 'installment_amount' in vals or \
           'payment_date' in vals or 'has_grace_period' in vals or \
           'grace_period_start_date' in vals or 'grace_period_end_date' in vals or \
           'installment' in vals or 'adjust_installment_amount' in vals:
            self._recompute_installments()
        return res

    # --- MODIFIED ORIGINAL METHOD ---
    def action_compute_installment(self):
        """ The button now simply calls our new helper method. """
        if self.installment_amount <= 0 and self.adjust_installment_amount:
            raise ValidationError(
                _("Amount Per Installment must be greater than zero."))
        self._recompute_installments()
        return True

    def action_approve(self):
        """
        This method overrides the original approval action to add a robust
        validation check. It ensures an employee cannot have more than one
        active (approved with a balance) loan at the same time.
        """
        for loan in self:
            other_active_loans = self.env['hr.loan'].search([
                ('employee_id', '=', loan.employee_id.id),
                ('state', '=', 'approve'),
                ('balance_amount', '!=', 0),
                ('id', '!=', loan.id)
            ])

            if other_active_loans:
                raise ValidationError(
                    _("Cannot approve this loan. Employee '%s' already has an active loan (%s) with a remaining balance.") %
                    (loan.employee_id.name, other_active_loans[0].name)
                )
        return super(HrLoan, self).action_approve()

    # --- OVERRIDE CREATE AND WRITE METHODS ---

    @api.model
    def create(self, vals):
        """ On creation, call the original create, then compute installments. """
        loan = super(HrLoan, self).create(vals)
        if loan.installment_amount > 0:
            loan._recompute_installments()
        return loan

    # def write(self, vals):
    #     """ On save/write, call the original write, then re-compute if necessary. """
    #     res = super(HrLoan, self).write(vals)
    #     # We only recompute if one of the key values has been changed.
    #     if 'loan_amount' in vals or 'installment_amount' in vals or 'payment_date' in vals:
    #         self._recompute_installments()
    #     return res

    # --- REQUIREMENT 2: VALIDATION LOGIC ---

    @api.constrains('loan_amount', 'state', 'manager_loan_type')
    def _check_loan_amount_policy(self):
        """
        This server-side validation enforces the company's loan policy limits.
        It now reads its values from the system configuration.
        """
        # Get the configuration parameter reading function
        get_param = self.env['ir.config_parameter'].sudo().get_param

        # Load all the policy values from the configuration at once
        emp_months = int(
            get_param('custom_loan_management.loan_policy_emp_months', default=4))
        emp_service_years_active = get_param(
            'custom_loan_management.loan_policy_emp_service_years', default='True').lower() == 'true'

        mgr_em_months = int(get_param(
            'custom_loan_management.loan_policy_mgr_emergency_months', default=6))
        mgr_em_service_years_active = get_param(
            'custom_loan_management.loan_policy_mgr_emergency_service_years', default='True').lower() == 'true'

        mgr_fa_months = int(get_param(
            'custom_loan_management.loan_policy_mgr_fixed_asset_months', default=24))

        for loan in self:

            if loan.is_special_loan:
                continue
            # We only run the check when the user tries to move it to the approval stage.
            if loan.state == 'waiting_approval_1' and loan.employee_id and loan.loan_amount > 0:
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', loan.employee_id.id),
                    ('state', '=', 'open')
                ], limit=1)

                if not contract:
                    raise ValidationError(
                        _("The employee does not have a running contract."))

                monthly_salary = contract.wage
                service_years = 0
                if contract.date_start:
                    service_years = relativedelta(
                        fields.Date.today(), contract.date_start).years

                max_loan_amount = 0
                policy_msg = ""

                if loan.is_employee_manager:
                    if not loan.manager_loan_type:
                        raise ValidationError(
                            _("You must select a 'Manager Loan Type' for this employee."))

                    if loan.manager_loan_type == 'emergency':
                        limit_by_salary = mgr_em_months * monthly_salary
                        # Only calculate service year limit if the setting is active
                        limit_by_service = service_years * \
                            monthly_salary if mgr_em_service_years_active and service_years > 0 else 0
                        max_loan_amount = max(
                            limit_by_salary, limit_by_service)
                        policy_msg = _("For a Manager Emergency Loan, the maximum amount is the greater of %(months)s months' salary (%(salary_limit)s) or service years x salary (%(service_limit)s).") % {
                            'months': mgr_em_months,
                            'salary_limit': f"{limit_by_salary:,.2f}",
                            'service_limit': f"{limit_by_service:,.2f}"
                        }

                    elif loan.manager_loan_type == 'fixed_asset':
                        max_loan_amount = mgr_fa_months * monthly_salary
                        policy_msg = _("For a Manager Fixed Asset Loan, the maximum amount is %(months)s months' salary (%(salary_limit)s).") % {
                            'months': mgr_fa_months,
                            'salary_limit': f"{max_loan_amount:,.2f}"
                        }

                else:  # Is a regular employee
                    limit_by_salary = emp_months * monthly_salary
                    # Only calculate service year limit if the setting is active
                    limit_by_service = service_years * \
                        monthly_salary if emp_service_years_active and service_years > 0 else 0
                    max_loan_amount = max(limit_by_salary, limit_by_service)
                    policy_msg = _("For an Employee Loan, the maximum amount is the greater of %(months)s months' salary (%(salary_limit)s) or service years x salary (%(service_limit)s).") % {
                        'months': emp_months,
                        'salary_limit': f"{limit_by_salary:,.2f}",
                        'service_limit': f"{limit_by_service:,.2f}"
                    }

                if loan.loan_amount > max_loan_amount:
                    raise ValidationError(_(
                        "Loan amount ({:,.2f}) exceeds company policy.\n\n"
                        "The maximum allowed is {:,.2f}.\n"
                        "Reason: {}"
                    ).format(loan.loan_amount, max_loan_amount, policy_msg))


class HrLoanLine(models.Model):
    _inherit = 'hr.loan.line'
    _order = 'date asc'

    loan_id = fields.Many2one(
        'hr.loan', string='Loan Ref.',
        help="Loan Reference", auto_join=True)

    paid_to_date_amount = fields.Monetary(
        string="Paid to Date",
        compute='_compute_paid_to_date_amount',
        store=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        related='loan_id.currency_id',
        store=True
    )

    @api.depends('paid', 'amount', 'loan_id.loan_line_ids.paid', 'loan_id.loan_line_ids.date')
    def _compute_paid_to_date_amount(self):

        for loan in self.mapped('loan_id'):
            cumulative_paid = 0.0
            # Sort by date, handling False/None values by treating them as minimum date
            for line in loan.loan_line_ids.sorted(key=lambda l: l.date if l.date else fields.Date.from_string('1900-01-01')):
                if line.paid:
                    cumulative_paid += line.amount
                line.paid_to_date_amount = cumulative_paid

    def write(self, vals):
        """
        When an installment line is changed (e.g., 'paid' is checked),
        this method will trigger the re-computation of the parent loan's totals.
        """
        loans_to_recompute = self.mapped('loan_id')

        res = super(HrLoanLine, self).write(vals)

        if 'paid' in vals and loans_to_recompute:
            loans_to_recompute._compute_loan_amount()

        return res


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        """Combined logic to handle Loan inputs and Pay-in-Cash policy"""
        """Combined logic to handle Loan inputs and Pay-in-Cash policy"""
        for payslip in self:
            # 1. Basic Validation
            if not payslip.employee_id or not payslip.date_from or not payslip.date_to:
                continue

            # 2. Find the Salary Rule for Loans (Code: LO)
            loan_salary_rule = payslip.struct_id.rule_ids.filtered(lambda x: x.code == 'LO')
            if not loan_salary_rule:
                continue

            # 3. Find the Input Type linked to this Salary Rule
            # We search by the custom 'input_id' field defined in your parent code
            input_type = self.env['hr.payslip.input.type'].search([
                ('input_id', '=', loan_salary_rule[0].id)
            ], limit=1)

            # FALLBACK: If no link found, search by Code 'LO'
            if not input_type:
                input_type = self.env['hr.payslip.input.type'].search([
                    ('code', '=', 'LO')
                ], limit=1)

            if not input_type:
                # If we still can't find an input type, we can't create the line.
                continue

            # 4. Check for approved loans
            loans = self.env['hr.loan'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('state', '=', 'approve'),
                ('pay_in_cash', '=', False) # NEW: Don't process if 'Pay in Cash' is checked
            ], order='create_date desc')

            # 5. Check if 'LO' already exists to avoid duplicates
            existing_input = payslip.input_line_ids.filtered(lambda r: r.input_type_id.code == 'LO')
            
            if not existing_input:
                for loan in loans:
                    for line in loan.loan_line_ids:
                        # Find unpaid installments for this period
                        if payslip.date_from <= line.date <= payslip.date_to and not line.paid:
                            # Add the line to the payslip
                            payslip.write({
                                'input_line_ids': [(0, 0, {
                                    'input_type_id': input_type.id,
                                    'amount': line.amount,
                                    'name': 'Loan Installment: ' + (loan.name or ''),
                                    'loan_line_id': line.id
                                })]
                            })

        return super(HrPayslip, self).compute_sheet()
