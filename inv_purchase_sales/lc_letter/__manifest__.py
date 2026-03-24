# -*- coding: utf-8 -*-
{
    'name': 'LC Letter of Credit',
    'summary': 'Manage Letters of Credit',
    'description': """
        Simple module to manage LC (Letter of Credit) documents.
        Track LC references, issuing banks, beneficiaries, amounts, and validity periods.
    """,
    'author': 'Niyat Consultancy',
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['base', 'contacts', 'purchase', 'mail', 'product', 'web', 'account', 'stock_landed_costs'],
    'license': 'LGPL-3',
    'application': True,
    # 'post_init_hook': 'lc_letter.hooks:post_init_hook',
    'data': [
        'security/lc_letter_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/lc_letter_stage_data.xml',
        'views/lc_letter_stage_views.xml',
        'views/lc_letter_payment_line_views.xml',
        'views/lc_letter_views.xml',
        'views/purchase_order_views.xml',
        'wizard/lc_letter_payment_request_views.xml',
        'report/report_payment_request.xml',
        'report/report_payment_request_template.xml',
    ],
}
