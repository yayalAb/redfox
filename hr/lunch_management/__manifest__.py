{
    'name': 'Lunch Management',
    'category': 'Human Resources',
    'summary': 'A module to manage lunch service',
    'depends': ['base', 'hr', 'hr_contract', 'hr_payroll'],
    'data': [
        'data/sequence.xml',
        'data/hr_salary_rule_data.xml',
        'security/user_group.xml',
        'security/ir.model.access.csv',
        'views/lunch_log_views.xml',
        'views/lunch_menus.xml',
        'views/product_variant_inherited_view.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,

}