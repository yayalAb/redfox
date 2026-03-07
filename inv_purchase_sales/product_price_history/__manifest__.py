{
    'name': 'Product Sales Price History',
    'version': '1.0',
    'summary': 'Tracks and displays the history of changes to a product\'s sales price.',
    'author': 'Henok Gm',
    'category': 'Sales/Sales',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
    ],
    'installable': True,
    'application': True,
}