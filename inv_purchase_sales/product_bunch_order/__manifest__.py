{
    'name': 'Product Bunch Order',
    'summary': 'Manage product grouping to order simply',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'depends': ['base', 'product', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_bunch_order_views.xml',
        'views/purchase_order_views.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
