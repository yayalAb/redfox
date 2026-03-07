{
    'name': "Supply Chain Validation",
    'category': 'Inventory',
    'summary': 'Validate supply chain processes',
    'description': 'This module provides validation for supply chain processes',
    'author': 'Niyat ERP',
    'depends': ['base', 'stock'],
    'data': [
        'views/supply_chain_validation_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}