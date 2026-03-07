# -*- coding: utf-8 -*-
from odoo import models, api
from dateutil.relativedelta import relativedelta


class HrContractReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_confirmation_letter_document'
    _description = 'Confirmation Letter Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        
        contracts = self.env['hr.contract'].browse(docids)
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(contract):
            ref_number = str(contract.id).zfill(4) if contract.id else '0000'
            return f"WG/{ref_number}/2018"
        
        # Calculate dates for the first contract (since we iterate in template)
        original_letter_date = False
        confirmation_date = False
        if contracts and contracts[0].date_start:
            # Original letter date: approximately 2 months and 7 days before start date
            original_letter_date = contracts[0].date_start - relativedelta(months=2, days=7)
            # Confirmation date: 3 months and 1 day after start date
            confirmation_date = contracts[0].date_start + relativedelta(months=3, days=1)
        
        original_letter_date_formatted = original_letter_date.strftime('%B %d, %Y') if original_letter_date else ''
        confirmation_date_formatted = confirmation_date.strftime('%B %d, %Y') if confirmation_date else ''
        
        # Get old reference number from context (passed from wizard)
        old_reference_number = self.env.context.get('old_reference_number', '')
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contracts,
            'original_letter_date': original_letter_date,
            'original_letter_date_formatted': original_letter_date_formatted,
            'confirmation_date': confirmation_date,
            'confirmation_date_formatted': confirmation_date_formatted,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
            'old_reference_number': old_reference_number,
        }


class HrContractMainReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_hr_contract_document'
    _description = 'Contract Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        
        contracts = self.env['hr.contract'].browse(docids)
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(contract):
            ref_number = str(contract.id).zfill(4) if contract.id else '0000'
            return f"WG/{ref_number}/2018"
        
        # Get expected response date from context (passed from wizard)
        expected_response_date = self.env.context.get('expected_response_date', False)
        expected_response_date_formatted = ''
        if expected_response_date:
            if hasattr(expected_response_date, 'strftime'):
                expected_response_date_formatted = expected_response_date.strftime('%d-%b-%Y')
            else:
                # If it's a string, try to parse it
                try:
                    if isinstance(expected_response_date, str):
                        date_obj = fields.Date.from_string(expected_response_date)
                        expected_response_date_formatted = date_obj.strftime('%d-%b-%Y')
                    else:
                        expected_response_date_formatted = str(expected_response_date)
                except:
                    expected_response_date_formatted = str(expected_response_date) if expected_response_date else ''
        
        # Helper function to format dates in DD-MMM-YYYY format
        def format_date(date_value):
            """Format a date value to DD-MMM-YYYY format"""
            if not date_value:
                return ''
            try:
                if hasattr(date_value, 'strftime'):
                    return date_value.strftime('%d-%b-%Y')
                elif isinstance(date_value, str):
                    date_obj = fields.Date.from_string(date_value)
                    return date_obj.strftime('%d-%b-%Y')
                else:
                    return str(date_value)
            except:
                return str(date_value) if date_value else ''
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contracts,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
            'expected_response_date': expected_response_date,
            'expected_response_date_formatted': expected_response_date_formatted,
            'format_date': format_date,
        }


class HrContractSalaryAdjustmentReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_salary_adjustment_document'
    _description = 'Salary Adjustment Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        
        contracts = self.env['hr.contract'].browse(docids)
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(contract):
            ref_number = str(contract.id).zfill(4) if contract.id else '0000'
            return f"WG/{ref_number}/2018"
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contracts,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
        }


class HrContractActingReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_acting_letter_document'
    _description = 'Acting Letter Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        
        contracts = self.env['hr.contract'].browse(docids)
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(contract):
            ref_number = str(contract.id).zfill(4) if contract.id else '0000'
            return f"WG/{ref_number}/2018"
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contracts,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
        }


class HrContractDelegationReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_delegation_duties_document'
    _description = 'Delegation of Duties Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        
        contracts = self.env['hr.contract'].browse(docids)
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(contract):
            ref_number = str(contract.id).zfill(4) if contract.id else '0000'
            return f"WG/{ref_number}/2018"
        
        # Get delegation values from context (passed from wizard)
        delegated_position = self.env.context.get('delegated_position', '')
        delegation_start_date = self.env.context.get('delegation_start_date', False)
        delegation_end_date = self.env.context.get('delegation_end_date', False)
        delegated_by_name = self.env.context.get('delegated_by_name', '')
        delegated_by_position = self.env.context.get('delegated_by_position', '')
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contracts,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
            'delegated_position': delegated_position,
            'delegation_start_date': delegation_start_date,
            'delegation_end_date': delegation_end_date,
            'delegated_by_name': delegated_by_name,
            'delegated_by_position': delegated_by_position,
        }


class HrContractExperienceReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_experience_letter_document'
    _description = 'Experience Letter Report'

    def _number_to_words(self, num):
        """Convert number to words"""
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

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        
        contracts = self.env['hr.contract'].browse(docids)
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(contract):
            ref_number = str(contract.id).zfill(4) if contract.id else '0000'
            return f"WG/{ref_number}/2025"
        
        # Get experience letter values from context (passed from wizard)
        basic_salary = self.env.context.get('basic_salary', 0.0)
        professional_allowance = self.env.context.get('professional_allowance', 0.0)
        transportation_allowance = self.env.context.get('transportation_allowance', 0.0)
        experience_end_date = self.env.context.get('experience_end_date', False)
        
        # Calculate gross salary
        gross_salary = basic_salary + professional_allowance + transportation_allowance
        
        # Convert to words
        basic_salary_words = self._number_to_words(int(basic_salary)) if basic_salary else ''
        professional_allowance_words = self._number_to_words(int(professional_allowance)) if professional_allowance else ''
        transportation_allowance_words = self._number_to_words(int(transportation_allowance)) if transportation_allowance else ''
        gross_salary_words = self._number_to_words(int(gross_salary)) if gross_salary else ''
        
        # Make number_to_words function available to template
        def number_to_words(num):
            return self._number_to_words(int(num)) if num else ''
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contracts,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
            'basic_salary': basic_salary,
            'professional_allowance': professional_allowance,
            'transportation_allowance': transportation_allowance,
            'gross_salary': gross_salary,
            'basic_salary_words': basic_salary_words,
            'professional_allowance_words': professional_allowance_words,
            'transportation_allowance_words': transportation_allowance_words,
            'gross_salary_words': gross_salary_words,
            'experience_end_date': experience_end_date,
            'number_to_words': number_to_words,
        }


class HrContractResignationAcceptanceReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_resign_accept'
    _description = 'Acceptance of Resignation Letter Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        from dateutil.relativedelta import relativedelta
        
        contracts = self.env['hr.contract'].browse(docids)
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(contract):
            ref_number = str(contract.id).zfill(4) if contract.id else '0000'
            return f"WG/{ref_number}/2025"
        
        # Get resignation acceptance values from context (passed from wizard)
        resignation_date = self.env.context.get('resignation_date', False)
        last_working_date = self.env.context.get('last_working_date', False)
        payment_effective_date = self.env.context.get('payment_effective_date', False)
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contracts,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
            'resignation_date': resignation_date,
            'last_working_date': last_working_date,
            'payment_effective_date': payment_effective_date,
            'relativedelta': relativedelta,
        }


class HrContractSalaryIncrementReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_salary_increment'
    _description = 'Salary Increment Report'

    def _number_to_words(self, num):
        """Convert number to words"""
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

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        
        contracts = self.env['hr.contract'].browse(docids)
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(contract):
            ref_number = str(contract.id).zfill(4) if contract.id else '0000'
            return f"WE/OT/{ref_number}/2025"
        
        # Get effective date from context (passed from wizard) or use contract date_start
        effective_date = self.env.context.get('effective_date', False)
        
        # Make number_to_words function available to template as fallback
        def number_to_words(num):
            return self._number_to_words(int(num)) if num else ''
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contracts,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
            'effective_date': effective_date,
            'number_to_words': number_to_words,
        }


class HrContractTemporaryAssignmentReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_temporary_assignment'
    _description = 'Temporary Assignment Letter Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        
        contracts = self.env['hr.contract'].browse(docids)
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(contract):
            ref_number = str(contract.id).zfill(4) if contract.id else '0000'
            return f"WG/OT/{ref_number}/2018"
        
        # Get temporary assignment values from context (passed from wizard)
        temporary_position = self.env.context.get('temporary_position', '')
        reports_to_position = self.env.context.get('reports_to_position', '')
        effective_date = self.env.context.get('effective_date', False)
        
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contracts,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
            'temporary_position': temporary_position,
            'reports_to_position': reports_to_position,
            'effective_date': effective_date,
        }