# -*- coding: utf-8 -*-
from odoo import models, api


class HrTrainingInvitationReport(models.AbstractModel):
    _name = 'report.hr_contract_letters.report_training_invitation_document'
    _description = 'Training Invitation Letter Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Provide report values to template"""
        from odoo import fields
        
        # Try to get training requisition model
        training_model = self.env.get('training.requisition')
        if not training_model:
            # Try alternative model names
            training_model = self.env.get('hr.training.requisition') or self.env.get('hr.training.request')
        
        if training_model and docids:
            trainings = training_model.browse(docids)
        elif docids:
            # Fallback: try direct browse if model lookup failed
            trainings = self.env['training.requisition'].browse(docids)
        else:
            trainings = self.env['training.requisition'].browse([])
        
        # Common values
        current_date = fields.Date.today()
        current_date_formatted = current_date.strftime('%B %d, %Y') if current_date else ''
        
        # Calculate Ref No
        def get_ref_no(training):
            ref_number = str(training.id).zfill(4) if training.id else '0000'
            return f"WG/{ref_number}/2018"
        
        # Helper function to safely get field value (without keyword args for QWeb compatibility)
        def safe_get(obj, *args):
            """Safely get a field value trying multiple field names
            Usage: safe_get(obj, 'field1', 'field2', 'field3', default_value)
            Last argument is treated as default if it's not a string field name
            """
            if not obj or not args:
                return None
            
            # Check if last arg is a default value (not a string or is a special marker)
            field_names = list(args)
            default = None
            
            # If last arg is not a string, treat it as default
            if len(field_names) > 1:
                last_arg = field_names[-1]
                # If it's explicitly None, empty list, or not a string, treat as default
                if last_arg is None or last_arg == [] or (not isinstance(last_arg, str) and not hasattr(last_arg, '__iter__')):
                    default = field_names.pop()
                elif isinstance(last_arg, str) and last_arg.startswith('default='):
                    # Handle 'default=value' string
                    default = None
                    field_names = [f for f in field_names if not f.startswith('default=')]
            
            for field_name in field_names:
                if not isinstance(field_name, str):
                    continue
                try:
                    value = getattr(obj, field_name, None)
                    if value:
                        return value
                except:
                    continue
            return default
        
        # Helper function to get participants list
        def get_participants(training):
            """Get participants from training requisition - uses training_participants field"""
            if not training:
                return self.env['hr.employee'].browse([])
            # Use training_participants field first, then fallback to other fields
            for field_name in ['training_participants', 'participants', 'participant_ids', 'employee_ids']:
                try:
                    if hasattr(training, field_name):
                        value = getattr(training, field_name, None)
                        if value:
                            # Ensure it's a recordset
                            if hasattr(value, '_model') or (hasattr(value, '__iter__') and not isinstance(value, (str, dict, list))):
                                return value
                            elif isinstance(value, list):
                                # Convert list to recordset if needed
                                if value and hasattr(value[0], 'id'):
                                    return self.env['hr.employee'].browse([p.id for p in value])
                except Exception as e:
                    import logging
                    _logger = logging.getLogger(__name__)
                    _logger.warning('Error getting participants from field %s: %s', field_name, str(e))
                    continue
            return self.env['hr.employee'].browse([])
        
        # Helper functions for common field access patterns
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
        
        # Helper function to format dates (handles both Date and Datetime)
        def format_date(date_value):
            """Format a date/datetime value to readable format (date only)"""
            if not date_value:
                return ''
            try:
                if hasattr(date_value, 'strftime'):
                    return date_value.strftime('%B %d, %Y')
                elif isinstance(date_value, str):
                    # Try datetime first, then date
                    try:
                        datetime_obj = fields.Datetime.from_string(date_value)
                        return datetime_obj.strftime('%B %d, %Y')
                    except:
                        try:
                            date_obj = fields.Date.from_string(date_value)
                            return date_obj.strftime('%B %d, %Y')
                        except:
                            return str(date_value)
                else:
                    return str(date_value)
            except:
                return str(date_value) if date_value else ''
        
        # Helper function to format datetime in user/record timezone (matches form display)
        def format_datetime_user_tz(record, datetime_value):
            """Convert datetime to user timezone and format as 'Month DD, YYYY at HH:MM AM/PM'"""
            if not datetime_value:
                return ''
            try:
                # Convert from UTC to user/company timezone (same as form view)
                local_dt = fields.Datetime.context_timestamp(record, datetime_value)
                return local_dt.strftime('%B %d, %Y at %I:%M %p')
            except Exception:
                return datetime_value.strftime('%B %d, %Y at %I:%M %p') if hasattr(datetime_value, 'strftime') else str(datetime_value)
        
        # Helper function to format datetime with time
        def format_datetime_with_time(datetime_value):
            """Format a datetime value to 'Month DD, YYYY HH:MM AM/PM' format"""
            if not datetime_value:
                return ''
            try:
                datetime_obj = None
                if isinstance(datetime_value, str):
                    datetime_obj = fields.Datetime.from_string(datetime_value)
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
        
        # Helper function to format time from datetime
        def format_time(datetime_value):
            """Extract and format time from datetime value (e.g., '2:45 PM')"""
            if not datetime_value:
                return ''
            try:
                # Convert to datetime object if needed
                datetime_obj = None
                if isinstance(datetime_value, str):
                    # Try to parse as datetime string (format: 'YYYY-MM-DD HH:MM:SS')
                    datetime_obj = fields.Datetime.from_string(datetime_value)
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
                import traceback
                # Uncomment for debugging: print(f"format_time error: {e}, value: {datetime_value}")
                return ''
        
        # Helper function to get first word of name
        def get_first_word(text, default=''):
            """Get first word from text"""
            if not text or not isinstance(text, str):
                return default
            parts = text.split()
            return parts[0] if parts else default
        
        # Safe wrapper function for formatting dates - completely self-contained
        def safe_format_datetime(datetime_value, prefer_time=True):
            """Safely format datetime with time if prefer_time is True, otherwise just date"""
            if not datetime_value:
                return '________________'
            
            try:
                # Convert to datetime object if needed
                datetime_obj = None
                if isinstance(datetime_value, str):
                    datetime_obj = fields.Datetime.from_string(datetime_value)
                elif hasattr(datetime_value, 'hour') and hasattr(datetime_value, 'minute'):
                    datetime_obj = datetime_value
                elif hasattr(datetime_value, 'strftime'):
                    # Check if it has time components
                    if hasattr(datetime_value, 'hour'):
                        datetime_obj = datetime_value
                    else:
                        # It's a date without time
                        if prefer_time:
                            # Try to get time from somewhere else, but if not, just format date
                            return datetime_value.strftime('%B %d, %Y')
                        else:
                            return datetime_value.strftime('%B %d, %Y')
                else:
                    return str(datetime_value) if datetime_value else '________________'
                
                if not datetime_obj:
                    # Fallback to date formatting
                    if hasattr(datetime_value, 'strftime'):
                        return datetime_value.strftime('%B %d, %Y')
                    return str(datetime_value) if datetime_value else '________________'
                
                # Format date
                date_str = datetime_obj.strftime('%B %d, %Y')
                
                # Format time if prefer_time is True
                if prefer_time:
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
                else:
                    return date_str
            except Exception as e:
                # Final fallback
                try:
                    if hasattr(datetime_value, 'strftime'):
                        return datetime_value.strftime('%B %d, %Y')
                    return str(datetime_value) if datetime_value else '________________'
                except:
                    return str(datetime_value) if datetime_value else '________________'
        
        return {
            'doc_ids': docids,
            'doc_model': training_model._name if training_model else 'training.requisition',
            'docs': trainings,
            'current_date': current_date,
            'current_date_formatted': current_date_formatted,
            'get_ref_no': get_ref_no,
            'format_date': format_date,
            'format_datetime_user_tz': format_datetime_user_tz,
            'format_time': format_time,
            'format_datetime_with_time': format_datetime_with_time,
            'safe_format_datetime': safe_format_datetime,  # Safe wrapper function
            'has_format_datetime_with_time': True,  # Flag to check if function exists
            'has_format_date': True,  # Flag to check if function exists
            'safe_get': safe_get,
            'get_first_word': get_first_word,
            'get_participants': get_participants,
            'get_training_field': get_training_field,
            'get_participant_field': get_participant_field,
        }
