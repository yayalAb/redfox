{
    'name': "Purchase Guarantee",
    'version': '1.0',
    'category': 'Purchases',
    'summary': "Manage purchase guarantees",
    'description': """
        This module allows users to manage purchase guarantees, including
        the creation and tracking of guarantees for purchased products.
    """,
    "author": "Niyat ERP",
    'depends': ['base', 'product', 'purchase', 'mail', 'hr_expense', 'VendorBid', 'payment_request'],
    'data': [

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}