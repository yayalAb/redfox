# -*- coding: utf-8 -*-
import base64
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrLoanSendWizard(models.TransientModel):
    _name = 'hr.loan.send.wizard'
    _description = 'Send Loan Agreement by Email'

    loan_id = fields.Many2one('hr.loan', string='Loan', required=True)
    partner_ids = fields.Many2many(
        'res.partner',
        'hr_loan_send_wizard_partner_rel',
        'wizard_id',
        'partner_id',
        string='Recipients (To)',
        required=True,
        help='Email addresses to send the loan agreement to'
    )
    cc_partner_ids = fields.Many2many(
        'res.partner',
        'hr_loan_send_wizard_cc_partner_rel',
        'wizard_id',
        'partner_id',
        string='CC',
        help='Email addresses to copy on the loan agreement'
    )
    subject = fields.Char(
        string='Subject',
        required=True,
        default=lambda self: _('Loan Agreement')
    )
    body = fields.Html(
        string='Message',
        help='Email body message'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            loan = self.env['hr.loan'].browse(self.env.context['active_id'])
            res['loan_id'] = loan.id
            
            # Set default recipient to employee (required)
            employee_partner = None
            if loan.employee_id:
                if loan.employee_id.work_email:
                    employee_partner = self.env['res.partner'].search([
                        ('email', '=', loan.employee_id.work_email)
                    ], limit=1)
                    if not employee_partner:
                        employee_partner = self.env['res.partner'].create({
                            'name': loan.employee_id.name,
                            'email': loan.employee_id.work_email,
                        })
                elif loan.employee_id.user_id and loan.employee_id.user_id.partner_id:
                    employee_partner = loan.employee_id.user_id.partner_id
                
                if employee_partner:
                    res['partner_ids'] = [(6, 0, [employee_partner.id])]
            
            # Set default subject
            if loan.employee_id:
                res['subject'] = _('Loan Agreement - %s') % loan.employee_id.name
            # Set default body
            res['body'] = self._get_default_body(loan)
        return res
    
    def _get_default_body(self, loan):
        """Generate default email body using QWeb template"""
        try:
            # Calculate monthly installment amount
            monthly_amount = 0.0
            if hasattr(loan, 'installment_amount') and loan.installment_amount:
                monthly_amount = loan.installment_amount
            elif loan.loan_line_ids and len(loan.loan_line_ids) > 0:
                # Get first unpaid installment amount
                unpaid_lines = loan.loan_line_ids.filtered(lambda l: not l.paid)
                if unpaid_lines:
                    monthly_amount = unpaid_lines[0].amount
                elif loan.loan_line_ids:
                    monthly_amount = loan.loan_line_ids[0].amount
            elif loan.installment and loan.installment > 0:
                monthly_amount = loan.loan_amount / loan.installment
            
            template_ref = 'hr_contract_letters.email_template_loan_agreement_body'
            template_values = {
                'loan': loan,
                'monthly_amount': monthly_amount,
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
            return _('Please find attached your loan agreement.')

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
        """Send loan agreement by email"""
        self.ensure_one()
        
        # Ensure employee is always in recipients
        employee_partner = None
        if self.loan_id.employee_id:
            if self.loan_id.employee_id.work_email:
                employee_partner = self.env['res.partner'].search([
                    ('email', '=', self.loan_id.employee_id.work_email)
                ], limit=1)
                if not employee_partner:
                    employee_partner = self.env['res.partner'].create({
                        'name': self.loan_id.employee_id.name,
                        'email': self.loan_id.employee_id.work_email,
                    })
            elif self.loan_id.employee_id.user_id and self.loan_id.employee_id.user_id.partner_id:
                employee_partner = self.loan_id.employee_id.user_id.partner_id
        
        # Add employee to recipients if not already there
        if employee_partner and employee_partner.id not in self.partner_ids.ids:
            self.partner_ids = [(4, employee_partner.id)]
        
        if not self.partner_ids:
            raise UserError(_('Please select at least one recipient.'))

        # Generate PDF report
        try:
            report_ref = 'hr_contract_letters.action_report_loan_agreement'
            pdf_content, dummy = self.env['ir.actions.report']._render_qweb_pdf(
                report_ref, 
                res_ids=[self.loan_id.id]
            )
            if not pdf_content:
                raise UserError(_('Failed to generate PDF. Please try again.'))
        except UserError:
            raise
        except Exception as e:
            raise UserError(_('Error generating PDF: %s. Please contact your administrator.') % str(e))

        # Create attachment for the PDF
        attachment = self.env['ir.attachment'].create({
            'name': _('Loan_Agreement_%s.pdf') % (self.loan_id.name or 'Loan'),
            'type': 'binary',
            'datas': base64.b64encode(pdf_content).decode('utf-8'),
            'res_model': 'hr.loan',
            'res_id': self.loan_id.id,
            'mimetype': 'application/pdf',
        })
        attachment_ids = [attachment.id]

        # Get email addresses
        to_emails = [p.email for p in self.partner_ids if p.email]
        cc_emails = [p.email for p in self.cc_partner_ids if p.email]
        
        # Get email_from
        email_from = self._get_email_from()
        if not email_from:
            raise UserError(_('No email address configured. Please configure an outgoing mail server or set your user email.'))

        # Create and send email using mail.mail
        mail_values = {
            'subject': self.subject,
            'body_html': self.body,
            'email_to': ','.join(to_emails) if to_emails else False,
            'email_cc': ','.join(cc_emails) if cc_emails else False,
            'email_from': email_from,
            'attachment_ids': [(6, 0, attachment_ids)],
            'model': 'hr.loan',
            'res_id': self.loan_id.id,
            'auto_delete': False,
        }
        
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        # Return success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Loan agreement has been sent by email successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_print_only(self):
        """Print/download PDF without sending email"""
        self.ensure_one()
        try:
            report_ref = 'hr_contract_letters.action_report_loan_agreement'
            report = self.env.ref(report_ref, raise_if_not_found=False)
            if not report or not report.exists():
                # Fallback: search for the report by name
                report = self.env['ir.actions.report'].search([
                    ('report_name', '=', 'hr_contract_letters.report_loan_agreement_document'),
                    ('model', '=', 'hr.loan')
                ], limit=1)
            if not report or not report.exists():
                raise UserError(_('Loan agreement report template not found. Please make sure the hr_contract_letters module is properly installed and updated.'))
            return report.report_action(self.loan_id)
        except UserError:
            raise
        except Exception as e:
            raise UserError(_('Error generating PDF: %s. Please contact your administrator.') % str(e))

