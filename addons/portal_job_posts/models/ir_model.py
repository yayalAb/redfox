# in models/ir_model.py
from odoo import models

class IrModel(models.Model):
    _inherit = 'ir.model'

    def _get_form_writable_fields(self, values=None):
        # First, get the default authorized fields from the parent method
        fields = super()._get_form_writable_fields(values)

        # If the form is for the 'hr.applicant' model, add your custom fields
        if self.model == 'hr.applicant':
            # List of all the custom fields you added in your form
            custom_field_names = [
                'current_address', 'date_of_birth', 'gender',
                'degree_level', 'graduation_department', 'university', 'graduation_year', 'cgpa',
                'exit_exam_result', 'experience_level', 'current_organization',
                'current_position', 'previous_job_start', 'previous_job_end',
                'current_salary', 'source_id', 'type_id', 'applicant_notes', 'salary_expected', 'availability',
            ]
            
            applicant_fields_obj = self.env['hr.applicant']._fields
            for field_name in custom_field_names:
                # Add the field to the authorized list if it's a valid field and not already in the list
                if field_name in applicant_fields_obj and field_name not in fields:
                    fields[field_name] = applicant_fields_obj[field_name].get_description(self.env)
        
        return fields