from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # --- Employee Policy Fields ---
    loan_policy_emp_months = fields.Integer(
        string="Employee: Salary Multiplier (Months)",
        config_parameter='custom_loan_management.loan_policy_emp_months',
        default=4,
        help="The number of months' salary an employee can take."
    )
    loan_policy_emp_service_years = fields.Boolean(
        string="Employee: Use Service Year Multiplier",
        config_parameter='custom_loan_management.loan_policy_emp_service_years',
        default=True,
        help="If checked, the max loan is the greater of (Salary Multiplier) OR (Service Years x Salary)."
    )

    # --- Manager Emergency Policy Fields ---
    loan_policy_mgr_emergency_months = fields.Integer(
        string="Manager (Emergency): Salary Multiplier (Months)",
        config_parameter='custom_loan_management.loan_policy_mgr_emergency_months',
        default=6
    )
    loan_policy_mgr_emergency_service_years = fields.Boolean(
        string="Manager (Emergency): Use Service Year Multiplier",
        config_parameter='custom_loan_management.loan_policy_mgr_emergency_service_years',
        default=True
    )
    
    # --- Manager Fixed Asset Policy Fields ---
    loan_policy_mgr_fixed_asset_months = fields.Integer(
        string="Manager (Fixed Asset): Salary Multiplier (Months)",
        config_parameter='custom_loan_management.loan_policy_mgr_fixed_asset_months',
        default=24
    )
    # Note: Service years are not applicable for this type per your requirement.