{
    'name': 'Hr Contract Customization',
    'category': 'Human Resources',
    'depends': ['hr_contract', 'hr', 'hr_payroll'],
    'data': [
        'views/hr_contract_view.xml',
        'data/hr_salary_rule_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_contract_customization/static/src/js/salary_widget.js',
            'hr_contract_customization/static/src/js/int_widget.js',
        ]
    },
    'installable': True,
    'auto_install': False,
}