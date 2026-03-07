# -*- coding: utf-8 -*-
import base64
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrContractSendWizard(models.TransientModel):
    _name = 'hr.contract.send.wizard'
    _description = 'Send Contract by Email'

    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)
    letter_type = fields.Selection(
        [
            ('offer', 'Job Offer Letter'),
            ('confirmation', 'Confirmation to Permanent Status'),
            ('job_description', 'Job Description'),
            ('contract_extension', 'Contract Employment Letter'),
            ('guarantee', 'Guarantee Letter'),
            ('acting', 'Acting Letter'),
            ('salary_adjustment', 'Salary &amp; Position Adjustment'),
            ('delegation', 'Delegation of Duties'),
            ('experience', 'Experience Letter'),
            ('resignation_acceptance', 'Acceptance of Resignation Letter'),
            ('salary_increment', 'Salary Increment'),
            ('temporary_assignment', 'Temporary Assignment Letter'),
        ],
        string='Letter Type',
        required=True,
        default='offer',
        help='Select the type of letter to send'
    )
    partner_ids = fields.Many2many(
        'res.partner',
        'hr_contract_send_wizard_partner_rel',
        'wizard_id',
        'partner_id',
        string='Recipients (To)',
        required=True,
        help='Email addresses to send the contract to'
    )
    cc_partner_ids = fields.Many2many(
        'res.partner',
        'hr_contract_send_wizard_cc_partner_rel',
        'wizard_id',
        'partner_id',
        string='CC',
        help='Email addresses to copy on the contract'
    )
    subject = fields.Char(
        string='Subject',
        required=True,
        default=lambda self: _('Employment Contract')
    )
    body = fields.Html(
        string='Message',
        help='Email body message'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help='Additional attachments to include in the email'
    )
    print_pdf = fields.Boolean(
        string='Print PDF',
        default=True,
        help='Download/Print PDF after sending email'
    )
    
    # Fields for Job Offer Letter
    expected_response_date = fields.Date(
        string='Expected Response Date',
        help='Date by which the candidate should respond to the job offer'
    )
    
    # Fields for Guarantee Letter
    guarantee_employee_name = fields.Char(
        string='Employee Name',
        help='Name of the employee for guarantee letter'
    )
    guarantee_company_name = fields.Char(
        string='Company Name',
        help='Name of the company for guarantee letter'
    )
    
    # Field for Confirmation Letter
    old_reference_number = fields.Char(
        string='Old Reference Number',
        help='Reference number from the original employment letter (e.g., WG/0341/18)'
    )
    
    # Fields for Delegation Letter
    delegated_position = fields.Char(
        string='Delegated Position',
        help='Position being delegated (e.g., Chief Executive Corporate Planning Officer)'
    )
    delegation_start_date = fields.Date(
        string='Delegation Start Date',
        help='Start date of the delegation period'
    )
    delegation_end_date = fields.Date(
        string='Delegation End Date',
        help='End date of the delegation period (leave empty for "until my return")'
    )
    delegated_by_name = fields.Char(
        string='Delegated By (Name)',
        help='Name of the person delegating the duties'
    )
    delegated_by_position = fields.Char(
        string='Delegated By (Position)',
        help='Position/title of the person delegating the duties'
    )
    
    # Fields for Experience Letter
    basic_salary = fields.Float(
        string='Basic Salary',
        digits=(16, 2),
        help='Monthly basic salary upon leaving the organization'
    )
    professional_allowance = fields.Float(
        string='Professional Allowance',
        digits=(16, 2),
        help='Monthly professional allowance'
    )
    transportation_allowance = fields.Float(
        string='Transportation Allowance',
        digits=(16, 2),
        help='Monthly transportation allowance'
    )
    experience_end_date = fields.Date(
        string='Experience End Date',
        help='End date of employment (if different from contract end date)'
    )
    
    # Fields for Acceptance of Resignation Letter
    resignation_date = fields.Date(
        string='Resignation Date',
        help='Date of the resignation letter'
    )
    last_working_date = fields.Date(
        string='Last Working Date',
        help='Last day of work'
    )
    payment_effective_date = fields.Date(
        string='Payment Effective Date',
        help='Date when payment will be finalized (usually day after last working date)'
    )
    
    # Fields for Salary Increment Letter
    new_salary = fields.Float(
        string='New Salary',
        digits=(16, 2),
        help='New basic salary amount'
    )
    salary_increment_effective_date = fields.Date(
        string='Effective Date',
        help='Date when the salary increment becomes effective'
    )
    
    # Fields for Temporary Assignment Letter
    temporary_position = fields.Many2one(
        'hr.job',
        string='Temporary Position',
        help='Position title for the temporary assignment'
    )
    reports_to_position = fields.Many2one(
        'hr.job',
        string='Reports To Position',
        help='Position title of the person they will report to'
    )
    temporary_assignment_effective_date = fields.Date(
        string='Effective Date',
        help='Date when the temporary assignment becomes effective'
    )
    
    @api.onchange('letter_type')
    def _onchange_letter_type(self):
        """Update subject and body when letter type changes"""
        if self.contract_id and self.contract_id.employee_id:
            if self.letter_type == 'confirmation':
                self.subject = _('Confirmation to Permanent Status - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
                # Don't clear old_reference_number - user may want to keep it
            elif self.letter_type == 'job_description':
                self.subject = _('Job Description - %s') % (self.contract_id.employee_id.job_id.name if self.contract_id.employee_id.job_id else self.contract_id.employee_id.name)
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            elif self.letter_type == 'contract_extension':
                self.subject = _('Contract Extension - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            elif self.letter_type == 'guarantee':
                self.subject = _('Guarantee Letter - %s') % self.contract_id.employee_id.name
            elif self.letter_type == 'acting':
                self.subject = _('Acting Letter - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            elif self.letter_type == 'salary_adjustment':
                self.subject = _('Salary &amp; Position Adjustment - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            elif self.letter_type == 'delegation':
                self.subject = _('Delegation of Duties - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            elif self.letter_type == 'experience':
                self.subject = _('Experience Letter - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            elif self.letter_type == 'resignation_acceptance':
                self.subject = _('Acceptance of Resignation Letter - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            elif self.letter_type == 'salary_increment':
                self.subject = _('Salary Increment - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            elif self.letter_type == 'temporary_assignment':
                self.subject = _('Temporary Assignment Letter - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            else:
                self.subject = _('Employment Contract - %s') % self.contract_id.employee_id.name
                self.guarantee_employee_name = False
                self.guarantee_company_name = False
            self.body = self._get_default_body(self.contract_id, self.letter_type)
    
    @api.onchange('guarantee_employee_name', 'guarantee_company_name')
    def _onchange_guarantee_fields(self):
        """Update body when guarantee letter fields change"""
        if self.letter_type == 'guarantee' and self.contract_id:
            self.body = self._get_default_body(self.contract_id, self.letter_type)
    
    @api.onchange('old_reference_number')
    def _onchange_old_reference_number(self):
        """Update body when old reference number changes"""
        if self.letter_type == 'confirmation' and self.contract_id:
            self.body = self._get_default_body(self.contract_id, self.letter_type)
    
    @api.constrains('partner_ids')
    def _check_employee_in_recipients(self):
        """Ensure employee is always in recipients"""
        for wizard in self:
            if wizard.contract_id.employee_id:
                employee_partner = None
                if wizard.contract_id.employee_id.work_email:
                    employee_partner = self.env['res.partner'].search([
                        ('email', '=', wizard.contract_id.employee_id.work_email)
                    ], limit=1)
                elif wizard.contract_id.employee_id.user_id:
                    employee_partner = wizard.contract_id.employee_id.user_id.partner_id
                
                if employee_partner and employee_partner.id not in wizard.partner_ids.ids:
                    wizard.partner_ids = [(4, employee_partner.id)]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            contract = self.env['hr.contract'].browse(self.env.context['active_id'])
            res['contract_id'] = contract.id
            
            # Set default recipient to employee (required)
            employee_partner = None
            if contract.employee_id:
                if contract.employee_id.work_email:
                    employee_partner = self.env['res.partner'].search([
                        ('email', '=', contract.employee_id.work_email)
                    ], limit=1)
                    if not employee_partner:
                        employee_partner = self.env['res.partner'].create({
                            'name': contract.employee_id.name,
                            'email': contract.employee_id.work_email,
                        })
                elif contract.employee_id.user_id and contract.employee_id.user_id.partner_id:
                    employee_partner = contract.employee_id.user_id.partner_id
                
                if employee_partner:
                    res['partner_ids'] = [(6, 0, [employee_partner.id])]
            
            # Set default CC recipients
            cc_partners = self._get_default_cc_partners(contract)
            if cc_partners:
                res['cc_partner_ids'] = [(6, 0, cc_partners.ids)]
            
            # Set default subject based on letter type
            letter_type = res.get('letter_type', 'offer')
            if contract.employee_id:
                if letter_type == 'confirmation':
                    res['subject'] = _('Confirmation to Permanent Status - %s') % contract.employee_id.name
                elif letter_type == 'job_description':
                    res['subject'] = _('Job Description - %s') % (contract.employee_id.job_id.name if contract.employee_id.job_id else contract.employee_id.name)
                elif letter_type == 'contract_extension':
                    res['subject'] = _('Contract Extension - %s') % contract.employee_id.name
                elif letter_type == 'guarantee':
                    res['subject'] = _('Guarantee Letter - %s') % contract.employee_id.name
                elif letter_type == 'acting':
                    res['subject'] = _('Acting Letter - %s') % contract.employee_id.name
                elif letter_type == 'salary_adjustment':
                    res['subject'] = _('Salary &amp; Position Adjustment - %s') % contract.employee_id.name
                elif letter_type == 'delegation':
                    res['subject'] = _('Delegation of Duties - %s') % contract.employee_id.name
                elif letter_type == 'experience':
                    res['subject'] = _('Experience Letter - %s') % contract.employee_id.name
                elif letter_type == 'temporary_assignment':
                    res['subject'] = _('Temporary Assignment Letter - %s') % contract.employee_id.name
                else:
                    res['subject'] = _('Employment Contract - %s') % contract.employee_id.name
            # Set default body
            res['body'] = self._get_default_body(contract, letter_type)
        return res
    
    def _get_default_cc_partners(self, contract):
        """Get default CC partners: department manager, Finance CEO, HR/General Service manager"""
        cc_partners = self.env['res.partner']
        
        # 1. Employee's department manager
        if contract.employee_id and contract.employee_id.department_id:
            dept = contract.employee_id.department_id
            if dept.manager_id:
                manager = dept.manager_id
                if manager.user_id and manager.user_id.partner_id:
                    cc_partners |= manager.user_id.partner_id
                elif manager.work_email:
                    partner = self.env['res.partner'].search([
                        ('email', '=', manager.work_email)
                    ], limit=1)
                    if not partner:
                        partner = self.env['res.partner'].create({
                            'name': manager.name,
                            'email': manager.work_email,
                        })
                    cc_partners |= partner
        
        # 2. Finance CEO Manager - Search for Finance department or CEO department
        finance_dept = self.env['hr.department'].search([
            '|',
            ('name', 'ilike', 'Finance'),
            '|',
            ('name', 'ilike', 'CEO'),
            ('name', 'ilike', 'Chief')
        ], limit=1)
        if finance_dept and finance_dept.manager_id:
            manager = finance_dept.manager_id
            if manager.user_id and manager.user_id.partner_id:
                cc_partners |= manager.user_id.partner_id
            elif manager.work_email:
                partner = self.env['res.partner'].search([
                    ('email', '=', manager.work_email)
                ], limit=1)
                if not partner:
                    partner = self.env['res.partner'].create({
                        'name': manager.name,
                        'email': manager.work_email,
                    })
                cc_partners |= partner
        
        # 3. HR and General Service Department Manager - Search for HR or General Service department
        hr_dept = self.env['hr.department'].search([
            '|',
            '|',
            ('name', 'ilike', 'HR'),
            ('name', 'ilike', 'Human Resource'),
            '|',
            ('name', 'ilike', 'General Service'),
            ('name', 'ilike', 'General Services')
        ], limit=1)
        if hr_dept and hr_dept.manager_id:
            manager = hr_dept.manager_id
            if manager.user_id and manager.user_id.partner_id:
                cc_partners |= manager.user_id.partner_id
            elif manager.work_email:
                partner = self.env['res.partner'].search([
                    ('email', '=', manager.work_email)
                ], limit=1)
                if not partner:
                    partner = self.env['res.partner'].create({
                        'name': manager.name,
                        'email': manager.work_email,
                    })
                cc_partners |= partner
        
        return cc_partners.filtered('email')

    def _get_ref_no(self, contract):
        """Generate reference number in format WG/XXXX/2018"""
        # Use contract ID padded to 4 digits, or use a sequence
        ref_number = str(contract.id).zfill(4) if contract.id else '0000'
        return f"WG/{ref_number}/2018"
    
    def _get_default_body(self, contract, letter_type='offer'):
        """Generate default email body using QWeb template"""
        from odoo import fields
        from datetime import datetime
        
        # Common values for all templates
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        ref_no = self._get_ref_no(contract)
        
        try:
            if letter_type == 'confirmation':
                # For confirmation letter
                from dateutil.relativedelta import relativedelta
                from datetime import datetime
                
                # Calculate dates for confirmation letter
                original_letter_date = False
                confirmation_date = False
                if contract.date_start:
                    # Original letter date: approximately 2 months and 7 days before start date
                    original_letter_date = contract.date_start - relativedelta(months=2, days=7)
                    # Confirmation date: 3 months and 1 day after start date
                    confirmation_date = contract.date_start + relativedelta(months=3, days=1)
                
                template_ref = 'hr_contract_letters.email_template_confirmation_body'
                original_letter_date_formatted = original_letter_date.strftime('%B %d, %Y') if original_letter_date else ''
                confirmation_date_formatted = confirmation_date.strftime('%B %d, %Y') if confirmation_date else ''
                template_values = {
                    'contract': contract,
                    'original_letter_date': original_letter_date,
                    'original_letter_date_formatted': original_letter_date_formatted,
                    'confirmation_date': confirmation_date,
                    'confirmation_date_formatted': confirmation_date_formatted,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                    'old_reference_number': self.old_reference_number or '',
                }
            elif letter_type == 'job_description':
                # For job description
                template_ref = 'hr_contract_letters.email_template_job_description_body'
                template_values = {
                    'contract': contract,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                }
            elif letter_type == 'contract_extension':
                # For contract extension
                template_ref = 'hr_contract_letters.email_template_contract_extension_body'
                template_values = {
                    'contract': contract,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                }
            elif letter_type == 'guarantee':
                # For guarantee letter
                template_ref = 'hr_contract_letters.email_template_guarantee_body'
                template_values = {
                    'contract': contract,
                    'guarantee_employee_name': self.guarantee_employee_name or '',
                    'guarantee_company_name': self.guarantee_company_name or '',
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                }
            elif letter_type == 'acting':
                # For acting letter
                template_ref = 'hr_contract_letters.email_template_acting_letter_body'
                # Define get_ref_no function for template
                def get_ref_no(contract):
                    return self._get_ref_no(contract)
                template_values = {
                    'contract': contract,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                    'get_ref_no': get_ref_no,
                }
            elif letter_type == 'salary_adjustment':
                # For salary adjustment letter
                template_ref = 'hr_contract_letters.email_template_salary_adjustment_body'
                # Define get_ref_no function for template
                def get_ref_no(contract):
                    return self._get_ref_no(contract)
                template_values = {
                    'contract': contract,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                    'get_ref_no': get_ref_no,
                    'previous_salary': getattr(self, 'previous_salary', None),
                    'salary_increment': getattr(self, 'salary_increment', None),
                }
            elif letter_type == 'delegation':
                # For delegation letter
                template_ref = 'hr_contract_letters.email_template_delegation_duties_body'
                # Define get_ref_no function for template
                def get_ref_no(contract):
                    return self._get_ref_no(contract)
                template_values = {
                    'contract': contract,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                    'get_ref_no': get_ref_no,
                    'delegated_position': getattr(self, 'delegated_position', None),
                    'delegation_start_date': getattr(self, 'delegation_start_date', None),
                    'delegation_end_date': getattr(self, 'delegation_end_date', None),
                    'delegated_by_name': getattr(self, 'delegated_by_name', None),
                    'delegated_by_position': getattr(self, 'delegated_by_position', None),
                }
            elif letter_type == 'experience':
                # For experience letter
                template_ref = 'hr_contract_letters.email_template_experience_letter_body'
                # Define get_ref_no function for template
                def get_ref_no(contract):
                    ref_number = str(contract.id).zfill(4) if contract.id else '0000'
                    return f"WG/{ref_number}/2025"
                
                # Get salary values
                basic_salary = getattr(self, 'basic_salary', 0.0) or 0.0
                professional_allowance = getattr(self, 'professional_allowance', 0.0) or 0.0
                transportation_allowance = getattr(self, 'transportation_allowance', 0.0) or 0.0
                gross_salary = basic_salary + professional_allowance + transportation_allowance
                
                # Number to words converter
                def number_to_words(num):
                    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
                            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
                            'Seventeen', 'Eighteen', 'Nineteen']
                    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
                    
                    if num == 0:
                        return 'Zero'
                    
                    def convert_hundreds(n):
                        if n == 0:
                            return ''
                        if n < 20:
                            return ones[n]
                        if n < 100:
                            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 else '')
                        return ones[n // 100] + ' Hundred' + (' ' + convert_hundreds(n % 100) if n % 100 else '')
                    
                    if num < 1000:
                        return convert_hundreds(num).strip()
                    
                    result = []
                    if num >= 1000000:
                        millions = num // 1000000
                        result.append(convert_hundreds(millions) + ' Million')
                        num %= 1000000
                    if num >= 1000:
                        thousands = num // 1000
                        result.append(convert_hundreds(thousands) + ' Thousand')
                        num %= 1000
                    if num > 0:
                        result.append(convert_hundreds(num))
                    
                    return ' '.join(result).strip()
                
                template_values = {
                    'contract': contract,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                    'get_ref_no': get_ref_no,
                    'basic_salary': basic_salary,
                    'professional_allowance': professional_allowance,
                    'transportation_allowance': transportation_allowance,
                    'gross_salary': gross_salary,
                    'basic_salary_words': number_to_words(int(basic_salary)) if basic_salary else '',
                    'professional_allowance_words': number_to_words(int(professional_allowance)) if professional_allowance else '',
                    'transportation_allowance_words': number_to_words(int(transportation_allowance)) if transportation_allowance else '',
                    'gross_salary_words': number_to_words(int(gross_salary)) if gross_salary else '',
                    'experience_end_date': getattr(self, 'experience_end_date', None),
                }
            elif letter_type == 'resignation_acceptance':
                # For acceptance of resignation letter
                template_ref = 'hr_contract_letters.email_template_resignation_acceptance_body'
                # Define get_ref_no function for template
                def get_ref_no(contract):
                    ref_number = str(contract.id).zfill(4) if contract.id else '0000'
                    return f"WG/{ref_number}/2025"
                template_values = {
                    'contract': contract,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                    'get_ref_no': get_ref_no,
                    'resignation_date': getattr(self, 'resignation_date', None),
                    'last_working_date': getattr(self, 'last_working_date', None),
                    'payment_effective_date': getattr(self, 'payment_effective_date', None),
                }
            elif letter_type == 'salary_increment':
                # For salary increment letter
                template_ref = 'hr_contract_letters.email_template_salary_increment_body'
                # Define get_ref_no function for template
                def get_ref_no(contract):
                    ref_number = str(contract.id).zfill(4) if contract.id else '0000'
                    return f"WE/OT/{ref_number}/2025"
                
                # Number to words converter as fallback
                def number_to_words(num):
                    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
                            'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
                            'Seventeen', 'Eighteen', 'Nineteen']
                    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
                    
                    if num == 0:
                        return 'Zero'
                    
                    def convert_hundreds(n):
                        if n == 0:
                            return ''
                        if n < 20:
                            return ones[n]
                        if n < 100:
                            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 else '')
                        return ones[n // 100] + ' Hundred' + (' ' + convert_hundreds(n % 100) if n % 100 else '')
                    
                    if num < 1000:
                        return convert_hundreds(num).strip()
                    
                    result = []
                    if num >= 1000000:
                        millions = num // 1000000
                        result.append(convert_hundreds(millions) + ' Million')
                        num %= 1000000
                    if num >= 1000:
                        thousands = num // 1000
                        result.append(convert_hundreds(thousands) + ' Thousand')
                        num %= 1000
                    if num > 0:
                        result.append(convert_hundreds(num))
                    
                    return ' '.join(result).strip()
                
                template_values = {
                    'contract': contract,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                    'get_ref_no': get_ref_no,
                    'effective_date': getattr(self, 'salary_increment_effective_date', None),
                    'number_to_words': number_to_words,
                }
            elif letter_type == 'temporary_assignment':
                # For temporary assignment letter
                template_ref = 'hr_contract_letters.email_template_temporary_assignment_body'
                # Define get_ref_no function for template
                def get_ref_no(contract):
                    ref_number = str(contract.id).zfill(4) if contract.id else '0000'
                    return f"WG/OT/{ref_number}/2018"
                temporary_position_obj = getattr(self, 'temporary_position', None)
                reports_to_position_obj = getattr(self, 'reports_to_position', None)
                template_values = {
                    'contract': contract,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                    'get_ref_no': get_ref_no,
                    'temporary_position': temporary_position_obj and temporary_position_obj.name or '',
                    'reports_to_position': reports_to_position_obj and reports_to_position_obj.name or '',
                    'effective_date': getattr(self, 'temporary_assignment_effective_date', None),
                }
            else:
                # For offer letter
                # Calculate response date (27 days before start date)
                response_date = False
                if contract.date_start:
                    from datetime import timedelta
                    response_date = contract.date_start - timedelta(days=27)
                
                # Get employee city safely
                employee_city = 'Addis Ababa'  # Default
                if contract.employee_id:
                    if hasattr(contract.employee_id, 'private_city') and contract.employee_id.private_city:
                        employee_city = contract.employee_id.private_city
                    elif contract.employee_id.address_id and contract.employee_id.address_id.city:
                        employee_city = contract.employee_id.address_id.city
                    elif hasattr(contract.employee_id, 'work_contact_id') and contract.employee_id.work_contact_id and contract.employee_id.work_contact_id.city:
                        employee_city = contract.employee_id.work_contact_id.city
                
                template_ref = 'hr_contract_letters.email_template_hr_contract_body'
                template_values = {
                    'contract': contract,
                    'response_date': response_date,
                    'employee_city': employee_city,
                    'current_date': current_date,
                    'current_date_formatted': current_date_formatted,
                    'ref_no': ref_no,
                }
            
            # Check if template exists
            template = self.env.ref(template_ref, raise_if_not_found=False)
            if not template:
                raise ValueError('Template %s not found' % template_ref)
            
            return self.env['ir.qweb']._render(template_ref, template_values)
        except Exception as e:
            # Log the error for debugging
            _logger.error('Error rendering email template: %s', str(e), exc_info=True)
            # Fallback to simple text if template not found
            if letter_type == 'confirmation':
                return _('Please find attached your confirmation letter.')
            elif letter_type == 'job_description':
                return _('Please find attached your job description.')
            elif letter_type == 'contract_extension':
                return _('Please find attached your contract extension letter.')
            elif letter_type == 'guarantee':
                return _('Please find attached your guarantee letter.')
            elif letter_type == 'acting':
                return _('Please find attached your acting letter.')
            elif letter_type == 'salary_adjustment':
                return _('Please find attached your salary adjustment letter.')
            elif letter_type == 'delegation':
                return _('Please find attached your delegation of duties letter.')
            elif letter_type == 'experience':
                return _('Please find attached your experience letter.')
            elif letter_type == 'resignation_acceptance':
                return _('Please find attached your acceptance of resignation letter.')
            elif letter_type == 'salary_increment':
                return _('Please find attached your salary increment letter.')
            elif letter_type == 'temporary_assignment':
                return _('Please find attached your temporary assignment letter.')
            return _('Please find attached your employment contract.')
    
    def _format_currency(self, amount, currency):
        """Format currency amount"""
        if not amount:
            return '0.00'
        return '{:,.2f} {}'.format(amount, currency.symbol or currency.name)
    
    def _get_email_from(self):
        """Get email_from from outgoing mail server configuration"""
        # Try to get from mail server configuration (from_filter)
        mail_server = self.env['ir.mail_server'].sudo().search([
            ('active', '=', True)
        ], order='sequence', limit=1)
        
        if mail_server and mail_server.from_filter:
            return mail_server.from_filter
        
        # Fallback to user's email or company email
        return self.env.user.email_formatted or self.env.company.email or False

    def action_send_email(self):
        """Send contract by email"""
        self.ensure_one()
        
        # Validate guarantee letter fields
        if self.letter_type == 'guarantee':
            if not self.guarantee_employee_name:
                raise UserError(_('Employee Name is required for Guarantee Letter.'))
            if not self.guarantee_company_name:
                raise UserError(_('Company Name is required for Guarantee Letter.'))
        
        # Ensure employee is always in recipients
        employee_partner = None
        if self.contract_id.employee_id:
            if self.contract_id.employee_id.work_email:
                employee_partner = self.env['res.partner'].search([
                    ('email', '=', self.contract_id.employee_id.work_email)
                ], limit=1)
                if not employee_partner:
                    employee_partner = self.env['res.partner'].create({
                        'name': self.contract_id.employee_id.name,
                        'email': self.contract_id.employee_id.work_email,
                    })
            elif self.contract_id.employee_id.user_id and self.contract_id.employee_id.user_id.partner_id:
                employee_partner = self.contract_id.employee_id.user_id.partner_id
        
        # Add employee to recipients if not already there
        if employee_partner and employee_partner.id not in self.partner_ids.ids:
            self.partner_ids = [(4, employee_partner.id)]
        
        if not self.partner_ids:
            raise UserError(_('Please select at least one recipient.'))

        # Generate PDF report based on letter type
        try:
            # Use report reference string based on letter type
            if self.letter_type == 'confirmation':
                report_ref = 'hr_contract_letters.action_report_confirmation_letter'
            elif self.letter_type == 'job_description':
                report_ref = 'hr_contract_letters.action_report_job_description'
            elif self.letter_type == 'contract_extension':
                report_ref = 'hr_contract_letters.action_report_contract_extension'
            elif self.letter_type == 'guarantee':
                report_ref = 'hr_contract_letters.action_report_guarantee'
            elif self.letter_type == 'acting':
                report_ref = 'hr_contract_letters.action_report_acting_letter'
            elif self.letter_type == 'salary_adjustment':
                report_ref = 'hr_contract_letters.action_report_salary_adjustment'
            elif self.letter_type == 'delegation':
                report_ref = 'hr_contract_letters.action_report_delegation_duties'
            elif self.letter_type == 'experience':
                report_ref = 'hr_contract_letters.action_report_experience_letter'
            else:
                report_ref = 'hr_contract_letters.action_report_hr_contract'
            # For guarantee letter, pass additional context
            report_context = {}
            if self.letter_type == 'guarantee':
                report_context = {
                    'guarantee_employee_name': self.guarantee_employee_name or '',
                    'guarantee_company_name': self.guarantee_company_name or '',
                }
            elif self.letter_type == 'confirmation':
                report_context = {
                    'old_reference_number': self.old_reference_number or '',
                }
            elif self.letter_type == 'delegation':
                report_context = {
                    'delegated_position': self.delegated_position or '',
                    'delegation_start_date': self.delegation_start_date or False,
                    'delegation_end_date': self.delegation_end_date or False,
                    'delegated_by_name': self.delegated_by_name or '',
                    'delegated_by_position': self.delegated_by_position or '',
                }
            elif self.letter_type == 'experience':
                report_context = {
                    'basic_salary': self.basic_salary or 0.0,
                    'professional_allowance': self.professional_allowance or 0.0,
                    'transportation_allowance': self.transportation_allowance or 0.0,
                    'experience_end_date': self.experience_end_date or False,
                }
            elif self.letter_type == 'resignation_acceptance':
                report_context = {
                    'resignation_date': self.resignation_date or False,
                    'last_working_date': self.last_working_date or False,
                    'payment_effective_date': self.payment_effective_date or False,
                }
            elif self.letter_type == 'salary_increment':
                report_context = {
                    'effective_date': self.salary_increment_effective_date or False,
                }
            elif self.letter_type == 'temporary_assignment':
                report_context = {
                    'temporary_position': self.temporary_position and self.temporary_position.name or '',
                    'reports_to_position': self.reports_to_position and self.reports_to_position.name or '',
                    'effective_date': self.temporary_assignment_effective_date or False,
                }
            else:
                report_context = {}
            
            pdf_content, dummy = self.env['ir.actions.report'].with_context(**report_context)._render_qweb_pdf(
                report_ref, 
                res_ids=[self.contract_id.id]
            )
            if not pdf_content:
                raise UserError(_('Failed to generate PDF. Please try again.'))
        except UserError:
            raise
        except Exception as e:
            raise UserError(_('Error generating PDF: %s. Please contact your administrator.') % str(e))

        # Create attachment for the PDF
        # Convert bytes to base64 string for storage
        if isinstance(pdf_content, bytes):
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        else:
            pdf_base64 = pdf_content
        
        attachment = self.env['ir.attachment'].create({
            'name': _('Contract_%s.pdf') % (self.contract_id.name or 'Contract'),
            'type': 'binary',
            'datas': pdf_base64,
            'res_model': 'hr.contract',
            'res_id': self.contract_id.id,
            'mimetype': 'application/pdf',
        })

        # Prepare attachments (only the PDF contract)
        attachment_ids = [attachment.id]

        # Prepare email addresses
        to_emails = self.partner_ids.filtered('email').mapped('email')
        cc_emails = self.cc_partner_ids.filtered('email').mapped('email')
        
        # Get email_from from outgoing mail server configuration
        email_from = self._get_email_from()
        
        # Send email using mail.mail to support CC
        mail_values = {
            'subject': self.subject,
            'body_html': self.body,
            'email_to': ','.join(to_emails) if to_emails else False,
            'email_cc': ','.join(cc_emails) if cc_emails else False,
            'email_from': email_from,
            'attachment_ids': [(6, 0, attachment_ids)],
            'model': 'hr.contract',
            'res_id': self.contract_id.id,
            'auto_delete': False,
        }
        
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        # Note: The mail.mail record will automatically create a message in the chatter
        # We don't need to call message_post separately, which would cause duplicate emails

        # Return success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Contract has been sent by email successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_print_only(self):
        """Print/download PDF without sending email"""
        self.ensure_one()
        
        # Validate guarantee letter fields
        if self.letter_type == 'guarantee':
            if not self.guarantee_employee_name:
                raise UserError(_('Employee Name is required for Guarantee Letter.'))
            if not self.guarantee_company_name:
                raise UserError(_('Company Name is required for Guarantee Letter.'))
        
        try:
            if self.letter_type == 'confirmation':
                report_ref = 'hr_contract_letters.action_report_confirmation_letter'
                report_name = 'hr_contract_letters.report_confirmation_letter_document'
            elif self.letter_type == 'job_description':
                report_ref = 'hr_contract_letters.action_report_job_description'
                report_name = 'hr_contract_letters.report_job_description_document'
            elif self.letter_type == 'contract_extension':
                report_ref = 'hr_contract_letters.action_report_contract_extension'
                report_name = 'hr_contract_letters.report_contract_extension_document'
            elif self.letter_type == 'guarantee':
                report_ref = 'hr_contract_letters.action_report_guarantee'
                report_name = 'hr_contract_letters.report_guarantee_document'
            elif self.letter_type == 'acting':
                report_ref = 'hr_contract_letters.action_report_acting_letter'
                report_name = 'hr_contract_letters.report_acting_letter_document'
            elif self.letter_type == 'salary_adjustment':
                report_ref = 'hr_contract_letters.action_report_salary_adjustment'
                report_name = 'hr_contract_letters.report_salary_adjustment_document'
            elif self.letter_type == 'delegation':
                report_ref = 'hr_contract_letters.action_report_delegation_duties'
                report_name = 'hr_contract_letters.report_delegation_duties_document'
            elif self.letter_type == 'experience':
                report_ref = 'hr_contract_letters.action_report_experience_letter'
                report_name = 'hr_contract_letters.report_experience_letter_document'
            elif self.letter_type == 'resignation_acceptance':
                report_ref = 'hr_contract_letters.action_report_resignation_acceptance'
                report_name = 'hr_contract_letters.report_resign_accept'
            elif self.letter_type == 'salary_increment':
                report_ref = 'hr_contract_letters.action_report_salary_increment'
                report_name = 'hr_contract_letters.report_salary_increment'
            elif self.letter_type == 'temporary_assignment':
                report_ref = 'hr_contract_letters.action_report_temporary_assignment'
                report_name = 'hr_contract_letters.report_temporary_assignment'
            else:
                report_ref = 'hr_contract_letters.action_report_hr_contract'
                report_name = 'hr_contract_letters.report_hr_contract_document'
            
            report = self.env.ref(report_ref, raise_if_not_found=False)
            if not report or not report.exists():
                # Fallback: search for the report by name
                report = self.env['ir.actions.report'].search([
                    ('report_name', '=', report_name),
                    ('model', '=', 'hr.contract')
                ], limit=1)
            if not report or not report.exists():
                raise UserError(_('Contract report template not found. Please make sure the hr_contract_letters module is properly installed and updated.'))
            
            # For guarantee letter, pass additional context
            if self.letter_type == 'offer':
                return report.with_context(
                    expected_response_date=self.expected_response_date or False
                ).report_action(self.contract_id)
            elif self.letter_type == 'guarantee':
                return report.with_context(
                    guarantee_employee_name=self.guarantee_employee_name or '',
                    guarantee_company_name=self.guarantee_company_name or ''
                ).report_action(self.contract_id)
            elif self.letter_type == 'confirmation':
                return report.with_context(
                    old_reference_number=self.old_reference_number or ''
                ).report_action(self.contract_id)
            elif self.letter_type == 'delegation':
                return report.with_context(
                    delegated_position=self.delegated_position or '',
                    delegation_start_date=self.delegation_start_date or False,
                    delegation_end_date=self.delegation_end_date or False,
                    delegated_by_name=self.delegated_by_name or '',
                    delegated_by_position=self.delegated_by_position or ''
                ).report_action(self.contract_id)
            elif self.letter_type == 'experience':
                return report.with_context(
                    basic_salary=self.basic_salary or 0.0,
                    professional_allowance=self.professional_allowance or 0.0,
                    transportation_allowance=self.transportation_allowance or 0.0,
                    experience_end_date=self.experience_end_date or False,
                ).report_action(self.contract_id)
            elif self.letter_type == 'resignation_acceptance':
                return report.with_context(
                    resignation_date=self.resignation_date or False,
                    last_working_date=self.last_working_date or False,
                    payment_effective_date=self.payment_effective_date or False,
                ).report_action(self.contract_id)
            elif self.letter_type == 'salary_increment':
                return report.with_context(
                    effective_date=self.salary_increment_effective_date or False,
                ).report_action(self.contract_id)
            elif self.letter_type == 'temporary_assignment':
                return report.with_context(
                    temporary_position=self.temporary_position and self.temporary_position.name or '',
                    reports_to_position=self.reports_to_position and self.reports_to_position.name or '',
                    effective_date=self.temporary_assignment_effective_date or False,
                ).report_action(self.contract_id)
            return report.report_action(self.contract_id)
        except UserError:
            raise
        except Exception as e:
            raise UserError(_('Error generating PDF: %s. Please contact your administrator.') % str(e))

