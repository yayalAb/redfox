# -*- coding: utf-8 -*-
import base64
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrTrainingInvitationSendWizard(models.TransientModel):
    _name = 'hr.training.invitation.send.wizard'
    _description = 'Send Training Invitation by Email'

    training_requisition_id = fields.Many2one(
        'training.requisition',
        string='Training Requisition',
        required=True,
        help='Training requisition to send invitation for'
    )
    partner_ids = fields.Many2many(
        'res.partner',
        'hr_training_invitation_send_wizard_partner_rel',
        'wizard_id',
        'partner_id',
        string='Recipients (To)',
        required=True,
        help='Email addresses to send the invitation to'
    )
    cc_partner_ids = fields.Many2many(
        'res.partner',
        'hr_training_invitation_send_wizard_cc_partner_rel',
        'wizard_id',
        'partner_id',
        string='CC',
        help='Email addresses to copy on the invitation'
    )
    subject = fields.Char(
        string='Subject',
        required=True,
        default=lambda self: _('Training Invitation')
    )
    body = fields.Html(
        string='Message',
        help='Email body message'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            training = self.env['training.requisition'].browse(self.env.context['active_id'])
            res['training_requisition_id'] = training.id
            
            # Get participants and create/find their partners - use training_participants field
            participants = getattr(training, 'training_participants', None) or getattr(training, 'participants', None) or getattr(training, 'participant_ids', None) or []
            partner_ids = []
            
            for participant in participants:
                # Get employee from participant (participant.lines has employee_id field)
                employee = None
                if hasattr(participant, 'employee_id') and participant.employee_id:
                    employee = participant.employee_id
                elif hasattr(participant, 'gender'):  # If participant is already an employee
                    employee = participant
                
                if not employee:
                    continue
                
                partner = None
                # Try multiple methods to get the partner
                # 1. Try related_partner_id (most common in Odoo)
                if hasattr(employee, 'related_partner_id') and employee.related_partner_id:
                    partner = employee.related_partner_id
                # 2. Try user_id.partner_id
                elif hasattr(employee, 'user_id') and employee.user_id and employee.user_id.partner_id:
                    partner = employee.user_id.partner_id
                # 3. Try work_contact_id
                elif hasattr(employee, 'work_contact_id') and employee.work_contact_id:
                    partner = employee.work_contact_id
                # 4. Try address_home_id
                elif hasattr(employee, 'address_home_id') and employee.address_home_id:
                    partner = employee.address_home_id
                # 5. Search by work_email
                elif hasattr(employee, 'work_email') and employee.work_email:
                    partner = self.env['res.partner'].search([
                        ('email', '=', employee.work_email)
                    ], limit=1)
                    # Create partner if not found
                    if not partner:
                        partner = self.env['res.partner'].create({
                            'name': employee.name,
                            'email': employee.work_email,
                        })
                # 6. Only create partner with email if available, skip if no email
                elif hasattr(employee, 'work_email') and employee.work_email:
                    # This case should not happen due to elif above, but just in case
                    partner = self.env['res.partner'].create({
                        'name': employee.name or 'Participant',
                        'email': employee.work_email,
                    })
                
                # Only add partner if it has an email address
                if partner and partner.email:
                    partner_ids.append(partner.id)
                elif partner:
                    _logger.warning('Skipping partner %s for participant %s - no email address', partner.name, employee.name if employee else 'Unknown')
            
            if partner_ids:
                res['partner_ids'] = [(6, 0, partner_ids)]
            
            # Set default subject
            program_name = getattr(training, 'program_name', None) or getattr(training, 'name', None) or 'Training Program'
            res['subject'] = _('Training Invitation - %s') % program_name
            
            # Set default body
            res['body'] = self._get_default_body(training)
        
        return res

    def _get_default_body(self, training):
        """Generate default email body using QWeb template"""
        try:
            template_ref = 'hr_contract_letters.email_template_training_invitation_body'
            
            # Get first participant for preview - use training_participants field
            participants = getattr(training, 'training_participants', None) or getattr(training, 'participants', None) or getattr(training, 'participant_ids', None) or []
            participant = participants[0] if participants else None
            
            # Helper functions for template
            def get_training_field(training, *field_names):
                """Get a field from training trying multiple names"""
                if not training:
                    return None
                for field_name in field_names:
                    try:
                        value = getattr(training, field_name, None)
                        if value:
                            return value
                    except:
                        continue
                return None
            
            def get_participant_field(participant, field_name, default=None):
                """Get a field from participant"""
                if not participant:
                    return default
                try:
                    return getattr(participant, field_name, default)
                except:
                    return default
            
            def format_date(date_value):
                """Format a date value to readable format"""
                if not date_value:
                    return ''
                try:
                    if hasattr(date_value, 'strftime'):
                        return date_value.strftime('%B %d, %Y')
                    elif isinstance(date_value, str):
                        from odoo import fields as odoo_fields
                        date_obj = odoo_fields.Date.from_string(date_value)
                        return date_obj.strftime('%B %d, %Y')
                    else:
                        return str(date_value)
                except:
                    return str(date_value) if date_value else ''
            
            def get_first_word(text, default=''):
                """Get first word from text"""
                if not text or not isinstance(text, str):
                    return default
                parts = text.split()
                return parts[0] if parts else default
            
            def get_ref_no(training):
                ref_number = str(training.id).zfill(4) if training.id else '0000'
                return f"WG/{ref_number}/2018"
            
            # Prepare template values
            current_date = fields.Date.today()
            template_values = {
                'training': training,
                'participant': participant,
                'get_ref_no': get_ref_no,
                'current_date': current_date,
                'current_date_formatted': current_date.strftime('%B %d, %Y') if current_date else '',
                'format_date': format_date,
                'ref_no': get_ref_no(training),
                'get_first_word': get_first_word,
                'get_training_field': get_training_field,
                'get_participant_field': get_participant_field,
            }
            
            # Check if template exists
            template = self.env.ref(template_ref, raise_if_not_found=False)
            if not template:
                raise ValueError('Template %s not found' % template_ref)
            
            # Render the template
            return self.env['ir.qweb']._render(template_ref, template_values)
        except Exception as e:
            # Log the error for debugging
            _logger.error('Error rendering email template: %s', str(e), exc_info=True)
            # Fallback to simple text if template not found
            return _('Please find attached your training invitation letter.')

    def action_send_email(self):
        """Send email to all recipients"""
        self.ensure_one()
        
        if not self.partner_ids:
            raise UserError(_('Please specify at least one recipient.'))
        
        training = self.training_requisition_id
        if not training:
            raise UserError(_('Please select a training requisition.'))
        
        # Get report action
        report_action = self.env.ref('hr_contract_letters.action_report_training_invitation', raise_if_not_found=False)
        if not report_action:
            raise UserError(_('Training invitation report not found.'))
        
        # Send email to each selected recipient (partner)
        email_from = self._get_email_from()
        sent_count = 0
        skipped_count = 0
        
        # Get all participants for PDF generation context
        all_participants = getattr(training, 'training_participants', None) or []
        
        _logger.info('Starting email send. Partner count: %d, Participants count: %d', len(self.partner_ids), len(all_participants))
        
        # Generate PDF once for all recipients (same PDF for all)
        pdf_content = None
        try:
            _logger.info('Generating PDF for training requisition ID: %s', training.id)
            pdf_result = report_action._render_qweb_pdf(
                report_action.report_name,
                res_ids=[training.id],
                data=None
            )
            pdf_content = pdf_result[0] if pdf_result else None
            if pdf_content:
                _logger.info('PDF generated successfully. Size: %d bytes', len(pdf_content))
            else:
                _logger.error('PDF generation returned empty content')
        except Exception as pdf_error:
            _logger.error('Error generating PDF: %s', str(pdf_error), exc_info=True)
            raise UserError(_('Could not generate PDF. Please check the server logs for details. Error: %s') % str(pdf_error))
        
        if not pdf_content:
            raise UserError(_('Could not generate PDF. Please try again or contact support.'))
        
        # Now send email to each recipient
        for partner in self.partner_ids:
            try:
                _logger.info('Processing partner %s (ID: %s) with email: %s', partner.name or 'Unknown', partner.id, partner.email or 'NO EMAIL')
                
                if not partner.email:
                    _logger.warning('Skipping partner %s (ID: %s) - no email address', partner.name or 'Unknown', partner.id)
                    skipped_count += 1
                    continue
                
                # Find the corresponding participant for this partner (for email template context)
                participant = None
                employee = None
                
                # Try to find employee from partner
                if hasattr(partner, 'employee_ids') and partner.employee_ids:
                    employee = partner.employee_ids[0]
                elif hasattr(partner, 'employee_id') and partner.employee_id:
                    employee = partner.employee_id
                
                # Find participant from training_participants that matches this employee
                if employee:
                    for p in all_participants:
                        if hasattr(p, 'employee_id') and p.employee_id and p.employee_id.id == employee.id:
                            participant = p
                            break
                
                # If no participant found, use first participant or None
                if not participant and all_participants:
                    participant = all_participants[0]
                
                # Get employee from participant if we have one
                if participant and hasattr(participant, 'employee_id') and participant.employee_id:
                    employee = participant.employee_id
                
                # Render email body with participant-specific content
                template_ref = 'hr_contract_letters.email_template_training_invitation_body'
                email_body = self.body
                try:
                    # Helper functions
                    def get_training_field(training, *field_names):
                        """Get a field from training trying multiple names"""
                        if not training:
                            return None
                        for field_name in field_names:
                            try:
                                value = getattr(training, field_name, None)
                                if value:
                                    return value
                            except:
                                continue
                        return None
                    
                    def get_participant_field(participant, field_name, default=None):
                        """Get a field from participant"""
                        if not participant:
                            return default
                        try:
                            return getattr(participant, field_name, default)
                        except:
                            return default
                    
                    def format_date(date_value):
                        """Format a date/datetime value to readable format (date only)"""
                        if not date_value:
                            return ''
                        try:
                            if hasattr(date_value, 'strftime'):
                                return date_value.strftime('%B %d, %Y')
                            elif isinstance(date_value, str):
                                from odoo import fields as odoo_fields
                                # Try datetime first, then date
                                try:
                                    datetime_obj = odoo_fields.Datetime.from_string(date_value)
                                    return datetime_obj.strftime('%B %d, %Y')
                                except:
                                    date_obj = odoo_fields.Date.from_string(date_value)
                                    return date_obj.strftime('%B %d, %Y')
                            else:
                                return str(date_value)
                        except:
                            return str(date_value) if date_value else ''
                    
                    def format_time(datetime_value):
                        """Extract and format time from datetime value (e.g., '2:45 PM')"""
                        if not datetime_value:
                            return ''
                        try:
                            from odoo import fields as odoo_fields
                            # Convert to datetime object if needed
                            datetime_obj = None
                            if isinstance(datetime_value, str):
                                # Try to parse as datetime string (format: 'YYYY-MM-DD HH:MM:SS')
                                datetime_obj = odoo_fields.Datetime.from_string(datetime_value)
                            elif hasattr(datetime_value, 'hour') and hasattr(datetime_value, 'minute'):
                                # Already a datetime object
                                datetime_obj = datetime_value
                            elif hasattr(datetime_value, 'strftime'):
                                # Might be a date object, try to convert
                                # If it's a date without time, return empty
                                if hasattr(datetime_value, 'hour'):
                                    datetime_obj = datetime_value
                                else:
                                    # It's a date object without time
                                    return ''
                            else:
                                return ''
                            
                            if not datetime_obj:
                                return ''
                            
                            hour = datetime_obj.hour
                            minute = datetime_obj.minute
                            
                            # Format as 12-hour time with AM/PM (e.g., "2:45 PM")
                            if hour == 0:
                                display_hour = 12
                                period = 'AM'
                            elif hour < 12:
                                display_hour = hour
                                period = 'AM'
                            elif hour == 12:
                                display_hour = 12
                                period = 'PM'
                            else:
                                display_hour = hour - 12
                                period = 'PM'
                            
                            return f"{display_hour}:{minute:02d} {period}"
                        except Exception as e:
                            # Return empty string on any error
                            return ''
                    
                    def format_datetime_with_time(datetime_value):
                        """Format a datetime value to 'Month DD, YYYY HH:MM AM/PM' format"""
                        if not datetime_value:
                            return ''
                        try:
                            from odoo import fields as odoo_fields
                            datetime_obj = None
                            if isinstance(datetime_value, str):
                                datetime_obj = odoo_fields.Datetime.from_string(datetime_value)
                            elif hasattr(datetime_value, 'hour') and hasattr(datetime_value, 'minute'):
                                datetime_obj = datetime_value
                            elif hasattr(datetime_value, 'strftime'):
                                # Check if it has time components
                                if hasattr(datetime_value, 'hour'):
                                    datetime_obj = datetime_value
                                else:
                                    # It's a date without time, just format the date
                                    return format_date(datetime_value)
                            else:
                                return format_date(datetime_value) if datetime_value else ''
                            
                            if not datetime_obj:
                                return format_date(datetime_value) if datetime_value else ''
                            
                            # Format date
                            date_str = datetime_obj.strftime('%B %d, %Y')
                            
                            # Format time
                            hour = datetime_obj.hour
                            minute = datetime_obj.minute
                            
                            if hour == 0:
                                display_hour = 12
                                period = 'AM'
                            elif hour < 12:
                                display_hour = hour
                                period = 'AM'
                            elif hour == 12:
                                display_hour = 12
                                period = 'PM'
                            else:
                                display_hour = hour - 12
                                period = 'PM'
                            
                            time_str = f"{display_hour}:{minute:02d} {period}"
                            return f"{date_str} {time_str}"
                        except Exception as e:
                            # Fallback to date only
                            return format_date(datetime_value) if datetime_value else ''
                    
                    def get_first_word(text, default=''):
                        if not text or not isinstance(text, str):
                            return default
                        parts = text.split()
                        return parts[0] if parts else default
                    
                    def get_ref_no(training):
                        ref_number = str(training.id).zfill(4) if training.id else '0000'
                        return f"WG/{ref_number}/2018"
                    
                    current_date = fields.Date.today()
                    template_values = {
                        'training': training,
                        'participant': participant,
                        'employee': employee,
                        'get_ref_no': get_ref_no,
                        'current_date': current_date,
                        'current_date_formatted': current_date.strftime('%B %d, %Y') if current_date else '',
                        'format_date': format_date,
                        'format_time': format_time,
                        'format_datetime_with_time': format_datetime_with_time,
                        'ref_no': get_ref_no(training),
                        'get_first_word': get_first_word,
                        'get_training_field': get_training_field,
                        'get_participant_field': get_participant_field,
                    }
                    email_body = self.env['ir.qweb']._render(template_ref, template_values)
                except Exception as e:
                    _logger.warning('Could not render email template for partner %s: %s', partner.name or 'Unknown', str(e))
                    # Use default body if template fails
                
                # Create attachment
                program_name = getattr(training, 'program_name', None) or 'Training Invitation'
                participant_name = employee.name if employee and employee.name else (partner.name or 'Participant')
                attachment_name = f'Training_Invitation_{participant_name.replace(" ", "_")}.pdf'
                attachment = self.env['ir.attachment'].create({
                    'name': attachment_name,
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'training.requisition',
                    'res_id': training.id,
                    'mimetype': 'application/pdf',
                })
                
                # Prepare email values
                email_values = {
                    'subject': self.subject,
                    'body_html': email_body,
                    'email_from': email_from,
                    'email_to': partner.email,
                    'attachment_ids': [(6, 0, [attachment.id])],
                }
                
                # Add CC recipients
                if self.cc_partner_ids:
                    cc_emails = [p.email for p in self.cc_partner_ids if p.email]
                    if cc_emails:
                        email_values['email_cc'] = ','.join(cc_emails)
                
                # Send email
                _logger.info('Creating mail for partner %s (email: %s)', partner.name, partner.email)
                mail = self.env['mail.mail'].create(email_values)
                mail.send()
                sent_count += 1
                _logger.info('Email sent successfully to %s. Total sent: %d', partner.email, sent_count)
                
            except Exception as e:
                partner_name = partner.name if 'partner' in locals() and partner else 'Unknown'
                _logger.error('Error sending email to partner %s: %s', partner_name, str(e), exc_info=True)
        
        # Return success message
        message = _('Training invitation emails sent to %d recipient(s).') % sent_count
        if skipped_count > 0:
            message += _(' %d recipient(s) skipped (no email address or PDF generation failed).') % skipped_count
        
        _logger.info('Email send completed. Sent: %d, Skipped: %d', sent_count, skipped_count)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success') if sent_count > 0 else _('Warning'),
                'message': message,
                'type': 'success' if sent_count > 0 else 'warning',
                'sticky': False,
            }
        }

    def action_print_only(self):
        """Print the training invitation letters"""
        self.ensure_one()
        
        training = self.training_requisition_id
        if not training:
            raise UserError(_('Please select a training requisition.'))
        
        # Get report action
        report_action = self.env.ref('hr_contract_letters.action_report_training_invitation', raise_if_not_found=False)
        if not report_action:
            raise UserError(_('Training invitation report not found.'))
        
        # Return report action
        return report_action.report_action([training.id])

    def _get_email_from(self):
        """Get email_from from outgoing mail server configuration (FROM Filtering)"""
        # Try to get from mail server configuration (from_filter)
        mail_server = self.env['ir.mail_server'].sudo().search([
            ('active', '=', True)
        ], order='sequence', limit=1)
        
        if mail_server and mail_server.from_filter:
            return mail_server.from_filter
        
        # Fallback to user's email or company email
        return self.env.user.email_formatted or self.env.company.email or False
