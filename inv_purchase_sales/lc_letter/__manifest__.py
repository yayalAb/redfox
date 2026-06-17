# -*- coding: utf-8 -*-
{
    'name': 'Foreign Payment Term Process',
    'summary': 'Manage foreign import payment terms: LC, CAD, and TT',
    'description': """
        Manage foreign payment instruments for import purchases:
        - Letter of Credit (Confirmed, Sight, Usance, Transferable)
        - Cash Against Documents (D/P Sight, D/A Usance, Partial Advance + CAD)
        - Advance Payment / TT (Partial and Full)
        Track references, banks, parties, amounts, payment lines, and vendor bills.
    """,
    'author': 'Niyat Consultancy',
    'category': 'Accounting',
    'version': '2.0.1',
    'depends': [
        'base',
        'contacts',
        'purchase',
        'mail',
        'product',
        'web',
        'account',
        'stock_landed_costs',
    ],
    'license': 'LGPL-3',
    'application': True,
    'assets': {
        'web.assets_backend': [
            'lc_letter/static/src/js/router_attachment_link_fix.js',
        ],
    },
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
