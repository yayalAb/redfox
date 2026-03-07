from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class SalaryGradeMatrixWizard(models.TransientModel):
    _name = 'salary.grade.matrix.wizard'
    _description = 'Salary Grade Matrix Entry Wizard'

    salary_grade_value_id = fields.Many2one(
        'salary.grade.value', string='Salary Grade', required=True,
        # Filter grades by the current user's company
        # domain="[('company_id', '=', company_id)]"
    )

    # We need to know which company we are working in.
    # company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    line_ids = fields.One2many(
        'salary.grade.matrix.line', 'wizard_id', string='Scale Levels'
    )

    @api.onchange('salary_grade_value_id')
    def _onchange_salary_grade_value_id(self):
        if not self.salary_grade_value_id:
            self.line_ids = [(5, 0, 0)]
            return

        scales = self.env['scale.level'].search([
            ('salary_grade_value_id', '=', self.salary_grade_value_id.id)
        ])
        existing_grades = self.env['salary.grade'].search([
            ('salary_grade_value_id', '=', self.salary_grade_value_id.id)
        ])
        
        # Create a map of scale_id -> {wage, salary_grade_id}
        grade_data_map = {
            grade.scale_level_id.id: {
                'wage': grade.wage,
                'id': grade.id
            } for grade in existing_grades
        }

        lines_data = []
        for scale in scales:
            # --- THIS LOGIC IS UPDATED ---
            grade_info = grade_data_map.get(scale.id, {})
            lines_data.append((0, 0, {
                'scale_level_db_id': scale.id,
                'scale_name': scale.name,
                # Get the wage or default to 0
                'wage': grade_info.get('wage', 0.0),
                # Get the salary_grade ID or default to 0
                'salary_grade_db_id': grade_info.get('id', 0),
            }))
            # --- END OF UPDATE ---
            
        self.line_ids = [(5, 0, 0)]
        self.line_ids = lines_data

    def action_process_and_save(self):
        self.ensure_one()
        grade_value = self.salary_grade_value_id
        # company_id = self.company_id.id

        # --- START OF DELETION LOGIC ---

        # 1. Get the initial state: All scale IDs for this grade from the DB
        initial_scale_records = self.env['scale.level'].search([
            ('salary_grade_value_id', '=', grade_value.id)
        ])
        initial_scale_ids = set(initial_scale_records.ids)

        # 2. Get the final state: All scale IDs present in the wizard lines
        final_scale_ids = set(line.scale_level_db_id for line in self.line_ids if line.scale_level_db_id)

        # 3. Find the difference: These are the IDs the user deleted from the list
        scale_ids_to_delete = initial_scale_ids - final_scale_ids

        if scale_ids_to_delete:
            # 4. Perform Deletion: Delete salary.grade records first to avoid constraint errors
            grades_to_delete = self.env['salary.grade'].search([
                ('salary_grade_value_id', '=', grade_value.id),
                ('scale_level_id', 'in', list(scale_ids_to_delete)),
            ])
            grades_to_delete.unlink()

            # Now delete the scale.level records themselves
            scales_to_delete = self.env['scale.level'].browse(scale_ids_to_delete)
            scales_to_delete.unlink()

        # --- END OF DELETION LOGIC ---

        # The existing validation and create/update logic follows...
        
        # Build a map of {id: original_name} for all remaining scales
        existing_scales = self.env['scale.level'].search([('salary_grade_value_id', '=', grade_value.id)])
        existing_scales_map = {scale.id: scale.name for scale in existing_scales}
        
        final_names = [line.scale_name.strip() for line in self.line_ids if line.scale_name]
        if len(final_names) != len(set(name.lower() for name in final_names)):
            raise ValidationError(_("You cannot have duplicate scale names within the same grade. Please review your entries."))
            
        for line in self.line_ids:
            scale_name = line.scale_name.strip() if line.scale_name else ''
            if not scale_name: continue

            if line.scale_level_db_id:
                original_name = existing_scales_map.get(line.scale_level_db_id)
                if scale_name != original_name and scale_name.lower() in {name.lower() for name in existing_scales_map.values()}:
                    raise ValidationError(_("The scale name '%s' already exists for this grade. Please choose a different name.", scale_name))
            else:
                if scale_name.lower() in {name.lower() for name in existing_scales_map.values()}:
                    raise ValidationError(_("The scale name '%s' already exists for this grade. Please choose a different name.", scale_name))

        for line in self.line_ids:
            scale_name = line.scale_name.strip() if line.scale_name else ''
            if not scale_name or not line.wage or line.wage <= 0:
                continue

            scale_level_record = None
            if line.scale_level_db_id:
                scale_level_record = self.env['scale.level'].browse(line.scale_level_db_id)
                if scale_level_record.name != scale_name:
                    scale_level_record.write({'name': scale_name})
            else:
                scale_level_record = self.env['scale.level'].create({
                    'name': scale_name,
                    'salary_grade_value_id': grade_value.id,
                })

            existing_grade = self.env['salary.grade'].search([
                ('salary_grade_value_id', '=', grade_value.id),
                ('scale_level_id', '=', scale_level_record.id),
                # ('company_id', '=', company_id), # CRITICAL FIX
            ], limit=1)

            vals = {
                'salary_grade_value_id': grade_value.id,
                'scale_level_id': scale_level_record.id,
                'wage': line.wage,
                'name': f"{grade_value.name} - {scale_name}",
                # 'company_id': company_id, # CRITICAL FIX
            }

            if existing_grade:
                if existing_grade.wage != line.wage:
                    # vals.pop('company_id', None)
                    existing_grade.write(vals)
            else:
                self.env['salary.grade'].create(vals)
        
        action = self.env['ir.actions.act_window']._for_xml_id('hr_payroll_grade.action_salary_grade')
        return action


class SalaryGradeMatrixLine(models.TransientModel):
    _name = 'salary.grade.matrix.line'
    _description = 'Salary Grade Matrix Wizard Line'

    wizard_id = fields.Many2one('salary.grade.matrix.wizard', string='Wizard', required=True, ondelete='cascade')
    
    # --- SIMPLIFIED FIELDS ---
    scale_level_db_id = fields.Integer(string="Scale Level DB ID", readonly=True)
    scale_name = fields.Char(string='Scale Name', required=True)
    # --- END OF CHANGES ---

    wage = fields.Monetary(
        string='Wage', currency_field='currency_id'
    )
    # currency_id = fields.Many2one(
    #     'res.currency', default=lambda self: self.env.company.currency_id
    # )
    currency_id = fields.Many2one('res.currency')

     # --- ADD THIS NEW FIELD ---
    salary_grade_db_id = fields.Integer(string="Salary Grade DB ID")
    # --- END OF ADDITION ---

    # --- ADD THIS NEW ACTION METHOD ---
    def action_go_to_grade_form(self):
        """
        This method is called by the new button.
        It does NOT save the wizard. It simply discards it and navigates
        to the full form view for the corresponding salary.grade record.
        """
        self.ensure_one()
        
        # A safeguard in case this is somehow clicked on a new line
        if not self.salary_grade_db_id:
            return {}

        # This dictionary is an instruction to the web client to open a new view.
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'salary.grade',
            'view_mode': 'form',
            'res_id': self.salary_grade_db_id,
            'target': 'current',  # This replaces the wizard with the form view
        }