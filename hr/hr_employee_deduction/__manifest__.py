{
    'name': 'Employee Ad-hoc Deductions',
    'version': '1.0',
    'summary': 'Manage and apply one-time deductions to employee payslips with an approval workflow.',
    'author': 'Henok Gm',
    'category': 'Human Resources/Payroll',
    'depends': [
        'hr_payroll',
        'mail',
    ],
    'data': [
        'security/hr_deduction_security.xml',
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',
        'views/employee_deduction_views.xml',
        'views/res_users_views.xml',
        'views/menu_items.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
