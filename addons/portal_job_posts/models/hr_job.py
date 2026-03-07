from odoo import models, fields

class HrJob(models.Model):
    _inherit = 'hr.job'

    # fields to control the dynamic visibility of fields in the portal
    x_show_graduation_department = fields.Boolean(string="Show Graduation Department", default=True)
    x_show_university = fields.Boolean(string="Show University/College", default=True)
    x_show_graduation_year = fields.Boolean(string="Show Graduation Year", default=True)
    x_show_cgpa = fields.Boolean(string="Show CGPA", default=True)
    x_show_exit_exam_result = fields.Boolean(string="Show Exit Exam Result", default=True)
    x_show_current_organization = fields.Boolean(string="Show Current Organization", default=True)
    x_show_current_position = fields.Boolean(string="Show Current Position", default=True)
    x_show_previous_job_start = fields.Boolean(string="Show Previous Job Start Date", default=True)
    x_show_previous_job_end = fields.Boolean(string="Show Previous Job End Date", default=True)
    x_show_current_salary = fields.Boolean(string="Show Current Salary", default=True)
    x_show_experience_level = fields.Boolean(string="Show Experience Level", default=True)

    x_required_graduation_department = fields.Boolean(string="required Graduation Department", default=True)
    x_required_university = fields.Boolean(string="required University/College", default=True)
    x_required_graduation_year = fields.Boolean(string="required Graduation Year", default=True)
    x_required_cgpa = fields.Boolean(string="required CGPA", default=True)
    x_required_exit_exam_result = fields.Boolean(string="required Exit Exam Result", default=True)
    x_required_current_organization = fields.Boolean(string="required Current Organization", default=True)
    x_required_current_position = fields.Boolean(string="required Current Position", default=True)
    x_required_previous_job_start = fields.Boolean(string="required Previous Job Start Date", default=True)
    x_required_previous_job_end = fields.Boolean(string="required Previous Job End Date", default=True)
    x_required_current_salary = fields.Boolean(string="required Current Salary", default=True)
    x_required_experience_level = fields.Boolean(string="required Experience Level", default=True)

