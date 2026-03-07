{
    'name': 'Custom Loan Management Policies',
    'version': '1.0',
    'summary': 'Adds advanced installment calculations and validation policies to the loan module.',
    'author': 'Your Name',
    'category': 'Human Resources/Payroll',
    'depends': [
        'hr_payroll',
        'ent_ohrms_loan',  # This is the correct dependency from the manifest you provided
    ],
    'data': [
        'views/hr_loan_views.xml',
        'views/res_config_settings_views.xml',
        'views/loan_config_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}