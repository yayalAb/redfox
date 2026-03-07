{
    'name': 'hr menu restructure',
    'version': '18.0',
    'sequence': 1,
    'summary': 'Niyat ERP  Base',
    'description': """
        This is a base module for  Modules.
            ========================================
    """,
    'category': 'Niyat ERP /Base',
    'website': 'https://www..et/',
    'license': 'LGPL-3',
    'depends': ['base', 'purchase', 'stock', 'sale', 'hr_payroll', 'hr_appraisal',
                'hr_employee_self_service', 'hr_resignation', 'hr_expense',
                'hr_holidays', 'planning', 'hr_attendance', 'hr', 'hr_dashboard'],
    'data': [
        'view/icons_view.xml'
    ],

    'demo': [],
    'installable': True,
    'price': 49.99,
    'currency': 'ETB',
    'application': True,
    'auto_install': False,

}
