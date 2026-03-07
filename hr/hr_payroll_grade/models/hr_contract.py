from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    salary_grade_value_id = fields.Many2one(
        'salary.grade.value', string='Salary Grade'
        # ==> ADD THIS DOMAIN <==
        # domain="[('company_id', '=', company_id)]"
    )

    scale_level_id = fields.Many2one(
        'scale.level', string='Scale Level',
        # domain="[('salary_grade_value_id','=',salary_grade_value_id)]",
        help="Filtered to the chosen Salary Grade Value"
    )

    has_deduction = fields.Boolean(string='Has Deduction')
    is_fixed_amount = fields.Boolean(string='Is Fixed Amount')
    fixed_amount = fields.Float(string='Fixed Amount')
    agreed_deduction = fields.Float(string='Amount(%)')

    # @api.onchange('salary_grade_value_id')
    # def _onchange_salary_grade_value(self):
    #     # clear scale when grade changes
    #     self.scale_level_id = False

    @api.onchange('scale_level_id')
    def _onchange_scale_level(self):
        if not self.scale_level_id:
            return
        # find the matching salary.grade
        search_domain = [
            ('salary_grade_value_id', '=', self.salary_grade_value_id.id),
            ('scale_level_id', '=', self.scale_level_id.id),
            # This is the crucial fix:
            # ('company_id', '=', self.company_id.id),
        ]
        sg = self.env['salary.grade'].search(search_domain, limit=1)
        if not sg:
            return
        # copy wage + allowances
        for fld in [
            'wage',
            'house_rent_allowance', 'dearness_allowance', 'travel_allowance',
            'meal_allowance', 'medical_allowance', 'position_allowance',
            'transport_home_allowance', 'transport_work_allowance', 'cash_indemnity_allowance',
            'fuel_allowance', 'professional_allowance', 'other_allowance',
        ]:
            setattr(self, fld, getattr(sg, fld))
