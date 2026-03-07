{
    'name': 'Hr Payroll Grade',
    'category': 'Human Resources',
    'summary': """Adds a salary grade and scale level to a contract.""",
    'author': 'Fikre',
    'depends': ['hr_contract', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/salary_grade_views.xml',
        'views/hr_contract_views.xml',
        'views/salary_grade_matrix_wizard_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}