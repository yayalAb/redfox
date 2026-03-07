{
    'name': 'Biennial Accrual for Time Off',
    'version': '1.0',
    'summary': "Adds an 'Every 2 years' frequency option to Accrual Plan Milestones.",
    'author': 'Henok Gm',
    'category': 'Human Resources/Time Off',
    'depends': ['hr_holidays'],
    'data': [
        'views/hr_leave_accrual_level_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}