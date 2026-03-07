{
    'name': 'HR Validation',
    'summary': 'Module for HR validation processes',
    'description': 'This module provides validation features for HR operations.',
    'author': 'Niyat ERP',   
    'category': 'Human Resources',
    'depends': ['hr', 'hr_contract_customization'],
    'data': [
        'views/hr_contract_inherited_view_form.xml',
        'views/hr_expense_inherited_view_form.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}