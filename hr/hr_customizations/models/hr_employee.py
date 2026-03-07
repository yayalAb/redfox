from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging  # It's good practice to import logging
import re

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # employee_id_no = fields.Char(
    #     string='Employee ID Number',
    #     readonly=False,
    #     copy=False,
    #     index=True,
    #     default=False
    # )

    _sql_constraints = [
        ('identification_id_unique', 'unique(identification_id)',
         'Employee ID Number must be unique!')
    ]

    """added the needed new field here"""
    emergency_relationship_id = fields.Many2one(
        comodel_name='hr.employee.relationship',
        string='Relationship',
        ondelete='restrict',
        help='Select the relationship of the emergency contact.'
    )

    """added employment status from contract"""
    employment_type = fields.Char(
        string="Employment Type",
        related="contract_id.contract_type_id.name",
        store=False,
        readonly=True,
        search="_search_employment_type"
    )

    job_grade = fields.Float(
        string='Job Grade',
        help='The grade or level of the job assigned to the employee.'
    )

    pension_no = fields.Char(
        string='Pension Number',
        help='The employee\'s pension (social security) number.'
    )

    tin_no = fields.Char(
        string='TIN Number',
        help='The employee\'s Taxpayer Identification Number.'
    )

    pays_pension = fields.Boolean(
        string="Pays Pension",
        default=True,
        help="Check this box if the employee contributes to a pension plan."
    )

    pays_costsharing = fields.Boolean(
        string="Pays Costsharing",
        default=False,
        help="Check this box if the employee is part of a cost-sharing agreement."
    )

    cost_sharing_type = fields.Selection(
        selection=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed Amount')
        ],
        string='Cost Sharing Type',
        help="Select whether the cost sharing is a percentage of a base amount or a fixed monetary value."
    )

    cost_sharing_amount_rate = fields.Float(
        string='Amount / Rate',
        digits='Account',  # Using 'Account' precision is good for monetary values
        help="The specific fixed amount or the percentage rate for the cost sharing."
    )

    cost_sharing_purpose = fields.Selection(
        selection=[
            ('education', 'Education'),
            # Other purposes can be added here in the future if needed
        ],
        string='Purpose',
        default='education',
        help="The reason for the cost sharing agreement, e.g., for educational support."
    )

    cost_sharing_start_date = fields.Date(
        string='Cost Sharing Start Date'
    )

    cost_sharing_end_date = fields.Date(
        string='Cost Sharing End Date',
        help="Optional: The date when this cost sharing agreement ends."
    )
    brach_id = fields.Many2one(
        'res.company',
        string='Branch',
        help="The branch where the employee is assigned."
    )

    use_others_account = fields.Boolean(
        string="Use Other's Account on bank letter",
        default=False,
        help="Check this box if the bank letter should use another person's account details."
    )
    other_account_name = fields.Char(
        string="Other's  Name",
        help="The name of the account holder if using another person's account."
    )
    other_account_number = fields.Char(
        string="Other's Account Number",
        help="The account number if using another person's account."
    )

    merged_with_other = fields.Boolean(
        string='Merged with Another Employee',
        default=False,
        help="Indicates if this employee record has been merged with another employee."
    )
    merged_employee_id = fields.Many2one(
        'hr.employee',
        string='Merged Employee',
        help="If this employee record was merged from another, this field links to the original employee."
    )
    other_employee = fields.Many2one(
        'hr.employee',
        string="Other Employee",
        help="Select another employee to view their details."
    )
    cost_center_id = fields.Many2one(
        'hr.cost.center',
        string="Cost Center",
        help="Employee Cost Center."
    )

    @api.depends('merged_with_other', 'merged_employee_id')
    def showmarged_employee(self):
        for rec in self:
            if rec.merged_with_other and rec.merged_employee_id:
                rec.merged_employee_id.write({
                    'other_employee': rec.id

                })

    @api.constrains('cost_sharing_type', 'cost_sharing_amount_rate')
    def _check_rate_or_amount(self):
        for rec in self:
            if rec.cost_sharing_type == 'percentage' and (rec.cost_sharing_amount_rate > 100 or rec.cost_sharing_amount_rate < 0):
                raise ValidationError("Percentage must be between 0 and 100%")
            if rec.cost_sharing_type == 'fixed' and (rec.cost_sharing_amount_rate < 0):
                raise ValidationError("Fixed Amount must be greater than 0.")

    bank_name = fields.Char(
        string="Bank Name",
        compute='_compute_bank_name',
        store=False,  # This field does not need to be stored
    )

    # ... (all your other existing fields like cost_sharing_type, etc.) ...

    # NEWLY ADDED COMPUTE METHOD
    @api.depends('bank_account_id.bank_id.name')
    def _compute_bank_name(self):
        """
        Computes the bank name from the employee's linked bank account.
        """
        for employee in self:
            if employee.bank_account_id and employee.bank_account_id.bank_id:
                employee.bank_name = employee.bank_account_id.bank_id.name
            else:
                employee.bank_name = False

    join_date = fields.Date(
        string="Join Date",
        compute="_compute_join_date",
        inverse="_inverse_join_date",
        store=True,
        required=False
    )

    factory_id = fields.Many2one(
        'hr.employee.factory',
        string='Factory',
        index=True,
        ondelete='restrict',
        help="The factory where the employee is assigned."
    )

    educational_status_id = fields.Many2one(
        'hr.educational.status', string='Educational Status')

    field_of_study_ids = fields.Many2many(
        'hr.field.study',
        'employee_field_study_rel',
        'employee_id',
        'field_study_id',
        string='Fields of Study',
        help='Academic disciplines or fields this employee has studied.'
    )

    experience_in_company = fields.Char(
        string="Experience (In Company)",
        help="The number of years of experience the employee has within this company."
    )

    experience_outside_company = fields.Char(
        string="Experience (Outside Company)",
        help="The number of years of relevant experience the employee has outside this company."
    )

    # =============Guarantor Fields ==============================
    guarantor_name = fields.Char(string="Guarantor's Name")
    guarantor_relationship_id = fields.Many2one(
        'hr.employee.relationship',
        string="Guarantor's Relationship"
    )
    guarantor_phone = fields.Char(string="Guarantor's Phone")
    guarantor_id_type_id = fields.Many2one(
        'hr.guarantor.id.type',
        string="Guarantor ID Type"
    )
    guarantor_id_number = fields.Char(string="Guarantor ID Number")
    guarantor_address = fields.Char(string="Guarantor's Address")

    # For the file upload, Odoo uses two fields
    guarantor_id_attachment_name = fields.Char(string="Guarantor ID Filename")
    guarantor_id_attachment = fields.Binary(
        string="Guarantor ID Upload",
        attachment=True
    )

    employee_status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('on_leave', 'On Leave'),
            ('terminated', 'Terminated'),
        ],
        string='Current Status',
        compute='_compute_employee_status',
        store=False,  # VERY IMPORTANT: This field should not be stored in the database
        help="Indicates the employee's current status. 'On Leave' is based on approved time off for today."
    )

    def _compute_employee_status(self):
        """
        Computes the employee's status based on their active state and current leaves.
        Priority: Terminated > On Leave > Active
        """
        today = fields.Date.today()
        for employee in self:
            # 1. Check if the employee is terminated (archived)
            if not employee.active:
                employee.employee_status = 'terminated'
                continue

            # 2. Check if the employee has an approved leave for today
            # We use search_count for better performance as we only need to know if one exists.
            is_on_leave = self.env['hr.leave'].search_count([
                ('employee_id', '=', employee.id),
                # The leave must be approved
                ('state', '=', 'validate'),
                # The leave must have started
                ('date_from', '<=', today),
                # The leave must not have ended
                ('date_to', '>=', today),
            ])

            if is_on_leave:
                employee.employee_status = 'on_leave'
            else:
                # 3. If not terminated and not on leave, they are active
                employee.employee_status = 'active'

    @api.depends('contract_ids.date_start')
    def _compute_join_date(self):
        for employee in self:
            if employee.join_date:
                continue
            earliest_date = False
            if employee.contract_ids:
                # Filter out contracts without a start date and find the minimum
                valid_contracts = employee.contract_ids.filtered(
                    lambda c: c.date_start)
                if valid_contracts:
                    earliest_date = min(valid_contracts.mapped('date_start'))

            employee.join_date = earliest_date

    def _inverse_join_date(self):
        # to let the user provide a value
        pass

    @api.model
    def _search_employment_type(self, operator, value):
        """
        When someone filters on employment_type, redirect to the
        contract_type name on the linked contract.
        """
        # operator will be things like 'ilike', '=', etc.
        # value is what the user typed.
        # We use a dotted path so Odoo knows to JOIN through the M2O.
        return [('contract_id.contract_type_id.name', operator, value)]

    """modified this to create a pop message upon successful creation of employee and also to link back to applicant/candidate to reflect the change on the recruitment app."""
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('identification_id'):
                vals['identification_id'] = self.env['ir.sequence'].next_by_code(
                    'employee.code') or 'Unassigned'

        # First, run the original create logic.
        employees = super(HrEmployee, self).create(vals_list)

        # to ensure that this is executed only when clicked 'create employee' button
        if self.env.context.get('create_from_applicant_flow'):
            _logger.info("Creating an Employee from the Applicant flow...")
            template_id = self.env.context.get(
                'contract_template_id_from_applicant')
            applicant_id = self.env.context.get('default_applicant_id')

            # We must check if we actually got an applicant ID from the context
            # and that exactly one employee was created, as our logic assumes this.
            if applicant_id and len(employees) == 1:
                # Find the original applicant record using the ID from the context.
                applicant = self.env['hr.applicant'].browse(applicant_id)
                if applicant.exists():
                    applicant.write({'employee_id': employees.id})
                    _logger.info(
                        f"Successfully linked Employee {employees.id} to Applicant {applicant.id}")
                    if template_id:
                        template = self.env['hr.contract'].browse(template_id)
                        start_date = self.env.context.get(
                            'contract_start_date_from_applicant')

                        contract_vals = {
                            'name': _("Contract for %s", employees.name),
                            'employee_id': employees.id,
                        }

                        # Conditionally add the start date if it was passed from the offer.
                        # The field on hr.contract is 'date_start'.
                        if start_date:
                            contract_vals['date_start'] = start_date
                            _logger.info(
                                f"Setting contract start date to {start_date} from applicant offer.")

                        # 1. Duplicate the template to create a new contract record.
                        # This avoids linking the shared template to our new employee.
                        new_contract = template.copy(contract_vals)

                        # 2. Set the contract to the 'Running' state.
                        new_contract.write({'state': 'open'})

                        _logger.info(
                            f"Created and activated contract {new_contract.id} for employee {employees.id} from template {template.id}.")
                    else:
                        _logger.warning(
                            f"No contract template ID was found in the context. No contract created for employee {employees.id}.")
                else:
                    _logger.warning(
                        f"Could not link Employee to Applicant {applicant_id} because the applicant was not found.")

        for employee in employees:
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'type': 'success',
                'message':  _("Employee '%s' has been created.", employee.name),
            })

        return employees

    """used for enforcing non circular reporting loops (meaning there is no cycle in the reporting line)"""
    @api.constrains('parent_id')
    def _check_no_circular_reporting(self):
        for employee in self:
            manager = employee.parent_id
            seen = set()
            # Traverse up the reporting chain
            while manager:
                # If we revisit the employee, circular reference detected
                if manager.id in seen or manager == employee:
                    raise ValidationError(
                        _('Circular reporting loop detected in the hierarchy for employee %s.')
                        % employee.name
                    )
                seen.add(manager.id)
                manager = manager.parent_id

    """used for enforcing the required fields"""
    @api.constrains(
        'name', 'work_phone', 'job_id', 'department_id'
    )
    def _check_required_employee_fields(self):
        for rec in self:
            pass
            # if not rec.name:
            #     raise ValidationError("The Full Name field cannot be empty.")
            # if not rec.work_phone:
            #     raise ValidationError("The Work Phone field cannot be empty.")
            # if not rec.job_id:
            #     raise ValidationError("The Position field cannot be empty.")
            # if not rec.department_id:
            #     raise ValidationError("The Department field cannot be empty.")

    @api.constrains('work_phone', 'emergency_phone')
    def _check_phone_format(self):
        """
        Validates the format of phone number fields on save:
        - 0XXXXXXXXX (10 digits starting with 0)
        - +251XXXXXXXXX (starts with +251 + 9 digits)
        - (+251)XXXXXXXXX (parenthesized +251 + 9 digits)
        - (XXX)-XXX-XXXX (US-style with parentheses and hyphens)
        """
        # pattern = re.compile(
        #     r'^(0\d{9}|\+251\d{9}|\(\+251\)\d{9}|\(\d{3}\)-\d{3}-\d{4})$')
        # for emp in self:
        #     for field in ('work_phone', 'emergency_phone'):
        #         value = getattr(emp, field)
        #         if value and not pattern.match(value):
        #             label = _('Work Phone') if field == 'work_phone' else _(
        #                 'Emergency Phone')
        #             message = _(
        #                 '%s "%s" is not valid.\nExamples:\n'
        #                 '• 0912345678\n'
        #                 '• +251912345678\n'
        #                 '• (+251)912345678\n'
        #                 '• (123)-456-7890'
        #             ) % (label, value)
        #             raise ValidationError(message)

    @api.constrains('work_email')
    def _check_email_format(self):
        """
        Validates the format of the work email address.
        """
        # A standard regex for email validation.
        email_regex = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        for employee in self:
            if employee.work_email and not email_regex.match(employee.work_email):
                raise ValidationError(_(
                    "The Work Email address '%s' is not a valid format."
                ) % employee.work_email)

    @api.constrains('name', 'emergency_contact')
    def _check_name_format(self):
        """
        Validates:
        - 'name' must start with a letter and may contain letters, numbers, or '@'.
        - 'emergency_contact' may only contain letters, spaces, or '/'.
        """
        name_pattern = re.compile(r'^[A-Za-z][A-Za-z0-9@/ ]*$')
        emergency_contact_pattern = re.compile(r'^[A-Za-z/ ]+$')

        # for emp in self:
        #     if emp.name and not name_pattern.match(emp.name):
        #         raise ValidationError(
        #             _("Full Name must start with a letter and contain only letters, numbers, '/', or '@'.")
        #         )
        #     if emp.emergency_contact and not emergency_contact_pattern.match(emp.emergency_contact):
        #         raise ValidationError(
        #             _("Emergency Contact Name must start with a letter and contain only letters, numbers, '/', or '@'.")
        #         )

    @api.constrains('job_id', 'department_id')
    def _check_job_and_department_name(self):
        """
        Ensures that the selected Job and Department names each contain
        at least one alphabetic character.
        """
        letter_pattern = re.compile(r'.*[A-Za-z].*')
        for rec in self:
            # Job
            if rec.job_id and not letter_pattern.match(rec.job_id.name or ''):
                raise ValidationError(_(
                    "The Position name '%s' must contain at least one letter."
                ) % rec.job_id.name)
            # Department
            if rec.department_id and not letter_pattern.match(rec.department_id.name or ''):
                raise ValidationError(_(
                    "The Department name '%s' must contain at least one letter."
                ) % rec.department_id.name)

    @api.constrains('emergency_relationship_id')
    def _check_emergency_relationship_name(self):
        """
        Ensures the selected emergency-relationship’s name:
          • only has letters, digits, spaces or '/'
          • contains at least one letter
          • may omit numbers or '/'
        """
        allowed_entire = re.compile(r'^[A-Za-z0-9/ ]+$')
        has_letter = re.compile(r'[A-Za-z]')

        for rec in self:
            rel = rec.emergency_relationship_id
            if not rel:
                continue
            name = rel.name or ''

            # 1) Only allowed characters
            if not allowed_entire.match(name):
                raise ValidationError(_(
                    "Relationship “%s” may only contain letters, digits, spaces or '/'."
                ) % name)

            # 2) Must have at least one letter
            if not has_letter.search(name):
                raise ValidationError(_(
                    "Relationship “%s” must contain at least one letter."
                ) % name)

    @api.constrains('mobile_phone')
    def _check_mobile_phone_format(self):
        pattern = re.compile(
            r'^(0\d{9}|\+251\d{9}|\(\+251\)\d{9}|\(\d{3}\)-\d{3}-\d{4})$')
        for emp in self:
            val = emp.mobile_phone
            if val and val.strip() and not pattern.match(val.strip()):
                raise ValidationError(_(
                    'Invalid mobile phone number: "%s".\n'
                    'Accepted formats include:\n'
                    ' - 0912345678\n'
                    ' - +251912345678\n'
                    ' - (+251)912345678\n'
                    ' - (123)-456-7890'
                ) % val)

    @api.constrains('job_grade')
    def _check_job_grade(self):
        for employee in self:
            if employee.job_grade < 0:
                raise ValidationError(_("Job Grade can't be Negative"))
