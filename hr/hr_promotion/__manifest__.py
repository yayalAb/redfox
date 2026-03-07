{
    'name': 'Hr Promotion',
    'category': 'Human Resources',
    'depends': [
        'hr_appraisal',
        'hr_contract',
        'hr_payroll',
    ],
    'data': [
        'security/hr_promotion_security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/hr_promotion_wizard_views.xml',
        'views/hr_promotion_views.xml',
        'views/hr_appraisal_views.xml'
    ],
    'installable': True,
    'auto_install': False,
}