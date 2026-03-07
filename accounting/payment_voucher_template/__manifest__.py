# -*- coding: utf-8 -*-
{
    'name': 'Payment Voucher Template',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Bank Payment Voucher Template for Accounting Payments',
    'description': '''
        This module adds a printable bank payment voucher template for accounting payments.
        Features:
        - Print payment voucher as PDF
        - Includes all payment details, allocations, and approval sections
    ''',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'report/payment_voucher_report.xml',
        'views/account_payment_view.xml',
    ],
    'installable': True,
    'installable': True,
    'auto_install': False,
    'application': False,
}

