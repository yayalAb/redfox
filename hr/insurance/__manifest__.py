{
    'name': 'Insurance',
    'version': '18.1',
    'summary': 'Insurance ',
    'description': """Insurance""",
    'category': '',
    'website': '',
    'depends': [
        'base',
        'hr',
        'base_setup',
        'mail',
    ],

    'license': 'LGPL-3',

    'data': [
        'security/ir.model.access.csv',
        'security/users_grups.xml',
        'data/data.xml',
        'data/send_mail.xml',
        'data/employee_expense_notification.xml',
        'views/coverage.xml',
        'views/insurance_providers.xml',
        'views/insurance_renewal_history.xml',
        'views/insurance_policy.xml',
        'views/employee_insurance.xml',
        'views/coverage_type.xml',
        'views/insurance_coverage_report.xml',
        'views/insurance_utilized_report.xml',
        # 'reports/coverage_utilization_report.xml',
        'views/copy_insurance_for_employee_view.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'insurance/static/src/scss/assets.scss',
        ],
    },
    'assets': {},
    'installable': True,
    'application': True,
}
