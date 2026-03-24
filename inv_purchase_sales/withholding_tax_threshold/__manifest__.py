# -*- coding: utf-8 -*-
{
    'name': "Withholding Tax Threshold",
    'summary': "Apply withholding tax only when total amount (before tax) exceeds threshold",
    'description': """
        This module conditionally applies withholding tax based on document total:
        - Applies withholding tax ONLY when amount_untaxed (subtotal before tax) > 20,000
        - Does NOT apply withholding when amount_untaxed <= 20,000
        - Threshold is based on total document amount, not per-line
        - Check is performed on amount before taxes (amount_untaxed)
        - Applies to: Invoices, Bills, Purchase Orders, and Purchase Quotations (RFQs)
    """,
    'author': "Niyat ERP",
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['account', 'purchase'],
    'data': [
        'data/ir_config_parameter_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
}
