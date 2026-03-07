import base64
import io
import zipfile
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EmployeeBank(models.Model):
    _inherit = 'res.partner.bank'

    company_id = fields.Many2one(
        'res.company', string='Company',
        readonly=False,
    )
    branch_address = fields.Char(string='Branch Address')
    is_payroll_account = fields.Boolean(
        string='Is Payroll Account',
        default=False,
        help="Check this box if this bank account is used for payroll purposes."
    )

    _sql_constraints = [
        ('unique_acc_number', 'UNIQUE(acc_number)', 'Account Number must be unique!')
    ]

    @api.constrains('acc_number', 'bank_id')
    def _check_required_fields(self):
        """Validate that bank and account number are required."""
        for bank in self:
            if not bank.bank_id:
                raise ValidationError(_('Bank is required. Please select a bank.'))
            if not bank.acc_number:
                raise ValidationError(_('Account Number is required. Please enter an account number.'))

    @api.constrains('acc_number')
    def _check_unique_acc_number(self):
        """Validate that account number is unique."""
        for bank in self:
            if bank.acc_number:
                duplicate = self.search([
                    ('acc_number', '=', bank.acc_number),
                    ('id', '!=', bank.id)
                ])
                if duplicate:
                    raise ValidationError(
                        _('Account Number "%s" already exists. Account numbers must be unique.')
                        % bank.acc_number
                    )


class BankStatementWizard(models.TransientModel):
    _name = 'hr.payroll.bank.statement.wizard'
    _description = 'Bank Statement Wizard'

    bank_ids = fields.Many2many(
        'res.partner.bank',
        string='Banks',
        required=True,
        help="Select one or more payroll bank accounts to generate statements for."
    )

    payslip_ids = fields.Many2many('hr.payslip', string='Payslips')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_model') == 'hr.payslip':
            res['payslip_ids'] = self.env.context.get('active_ids', [])
        return res

    def chunk_list(self, lst, chunk_size=35):
        """Helper to split list into chunks of chunk_size"""
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    @api.model
    def format_amount_to_text(self, amount, currency):
        """
        Format amount to text with minimized 'and' words for better readability.
        Removes excessive 'and' words while keeping necessary ones before currency and cents.
        Example: "Five Million, Seven Hundred And One Thousand, Two Hundred And Twenty Birr and Ninety Cents"
        Becomes: "Five Million, Seven Hundred One Thousand, Two Hundred Twenty Birr and Ninety Cents"
        """
        if not currency:
            return str(amount)
        
        # Get the standard amount_to_text
        amount_text = currency.amount_to_text(amount)
        
        # Clean up excessive "and" words
        import re
        
        # Split the text to preserve "and" before currency and cents
        # Find the position where currency name appears (Birr, Dollar, etc.)
        currency_pattern = r'\s+(Birr|Dollar|Pound|Euro|Yen|Yuan|Rupee|Peso|Krone|Franc|Lira|Ruble|Won|Baht|Ringgit|Dinar|Dirham|Riyal|Shekel|Rial|Taka|Kyat|Riel|Kip|Dong|Rupiah|Tugrik|Som|Tenge|Manat|Lari|Dram|Lek|Mark|Lev|Kuna|Zloty|Koruna|Forint|Leu|Lei|Denar|Shekel|Rial|Ringgit|Baht|Won|Ruble|Lira|Franc|Krone|Peso|Rupee|Yuan|Yen|Euro|Pound|Dollar|Birr)'
        match = re.search(currency_pattern, amount_text, re.IGNORECASE)
        
        if match:
            # Split into number part and currency/cents part
            split_pos = match.start()
            number_part = amount_text[:split_pos]
            currency_part = amount_text[split_pos:]
            
            # Remove "And" between number groups in the number part
            # Remove "Hundred And" followed by numbers
            number_part = re.sub(r'\bHundred\s+And\s+', 'Hundred ', number_part, flags=re.IGNORECASE)
            
            # Remove "Thousand And", "Million And", etc. followed by numbers
            number_part = re.sub(r'\b(Thousand|Million|Billion|Trillion)\s+And\s+', r'\1 ', number_part, flags=re.IGNORECASE)
            
            # Clean up multiple spaces
            number_part = re.sub(r'\s+', ' ', number_part)
            
            # Clean up spaces around commas
            number_part = re.sub(r'\s*,\s*', ', ', number_part)
            
            # Recombine
            amount_text = number_part + currency_part
        else:
            # If no currency found, just clean up "And" between number groups
            amount_text = re.sub(r'\bHundred\s+And\s+', 'Hundred ', amount_text, flags=re.IGNORECASE)
            amount_text = re.sub(r'\b(Thousand|Million|Billion|Trillion)\s+And\s+', r'\1 ', amount_text, flags=re.IGNORECASE)
            amount_text = re.sub(r'\s+', ' ', amount_text)
        
        # Capitalize first letter
        if amount_text:
            amount_text = amount_text[0].upper() + amount_text[1:] if len(amount_text) > 1 else amount_text.upper()
        
        return amount_text.strip()

    def action_generate_report(self):
        """
        Prepare data for all selected banks, splitting payslips into pages of 35 rows,
        with page totals and grand total for all pages.
        """
        self.ensure_one()

        if not self.payslip_ids:
            raise UserError(_("You must select at least one payslip."))

        reports_data = []
        all_payslip_ids = self.env['hr.payslip'].browse([])

        for bank_account in self.bank_ids:
            if not bank_account.bank_id:
                continue
            
            # Get the bank_id from the selected bank account
            bank_id = bank_account.bank_id.id
            
            # Find payslips where employee has any bank account with this bank_id
            # Use default parameter to capture bank_id value correctly in lambda
            payslips_for_bank = self.payslip_ids.filtered(
                lambda p, bid=bank_id: (
                    p.employee_id.bank_account_ids and 
                    bid in p.employee_id.bank_account_ids.mapped('bank_id').ids and 
                    not p.employee_id.merged_with_other
                )
            )

            if not payslips_for_bank:
                continue

            all_payslip_ids |= payslips_for_bank

            # Sort payslips if needed (by employee name for example)
            payslips_sorted = payslips_for_bank.sorted(
                key=lambda p: p.employee_id_no)

            # Chunk payslips into pages of 35 rows each
            payslip_pages = list(self.chunk_list(payslips_sorted, 35))

            # Calculate page totals for each chunk
            page_totals = []
            for page in payslip_pages:
                page_total = sum(p._get_salary_line_total(
                    'NET') + p.marged_net for p in page)
                page_totals.append(page_total)

            # Calculate grand total (all payslips)
            grand_total = sum(p._get_salary_line_total(
                'NET') + p.marged_net for p in payslips_for_bank)

            # Prepare report dict with pages, page totals and grand total
            reports_data.append({
                'bank_id': bank_account.id,
                'branch_address': bank_account.branch_address,
                'payslip_pages': [[p.id for p in page] for page in payslip_pages],
                'page_totals': page_totals,
                'grand_total': grand_total,
                'company_id': payslips_for_bank[0].company_id.id,
            })

        if not reports_data:
            raise UserError(
                _("There are no payslips matching any of the selected banks in your selection."))

        data = {
            'reports': reports_data,
        }

        report_action = self.env.ref(
            'hr_payroll_bank_statement.action_report_bank_statement')

        return report_action.report_action(all_payslip_ids, data=data)
