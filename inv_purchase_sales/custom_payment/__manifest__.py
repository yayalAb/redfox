# -*- coding: utf-8 -*-
{
    'name': 'Custom Payment',
    'summary': 'Custom payment methods (Cash, Cheque, CPO, Tele Birr) and maturity date',
    'description': """
        - Predefined payment methods: Cash, Cheque, CPO, Tele Birr (inbound & outbound)
        - Create additional payment methods from Configuration or journal setup
        - Maturity Date on payment form and register payment wizard
    """,
    'author': 'Niyat ERP',
    'category': 'Accounting',
    'version': '18.0.1.0.8',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_method_data.xml',
        'views/account_payment_method_views.xml',
        'views/account_journal_views.xml',
        'views/account_payment_views.xml',
        'views/account_payment_register_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
