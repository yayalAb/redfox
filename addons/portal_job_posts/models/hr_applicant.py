from odoo import models, fields, api

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'
    _description = 'Applicant Detail'

    current_address = fields.Char(string="Current Address")
    date_of_birth = fields.Date(string="Date of Birth")
    
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender")

    graduation_department = fields.Char(string="Department Graduated From")
    university = fields.Char(string="University/College")
    graduation_year = fields.Char(string="Year of Graduation")

    cgpa = fields.Float(string="CGPA", digits=(3, 2))
    exit_exam_result = fields.Char(string="Exit Exam Result")

    experience_level = fields.Selection([
        ('junior', 'Junior'),
        ('intermediate', 'Intermediate'),
        ('senior', 'Senior'),
    ], string="Experience Level")

    current_organization = fields.Char(string="Current Organization")
    current_position = fields.Char(string="Current Position Title")

    previous_job_start = fields.Date(string="Previous Job Start Date")
    previous_job_end = fields.Date(string="Previous Job End Date")

    current_salary = fields.Monetary(string="Current Salary")
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

