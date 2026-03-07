{
    'name': 'Hr Payroll Difference Analysis',
    'category': 'Human Resources',
    'summary': 'A module to analyze payroll differences between months',
    'depends': [
        'base', 'hr_payroll', 'hr_contract',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/payroll_differece_view.xml',


    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
