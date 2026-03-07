{
    'name': 'Store Request',
    'summary': 'manage store',
    'description': 'A module to handle store and purchase requests in Odoo',
    'author': 'Niyat Consultancy.',
    'depends': ['base', 'stock', 'hr', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_group.xml',
        'data/data.xml',
        'report/store_request_report_template.xml',
        'views/store_request.xml',
        'views/stock_wahehouse_view.xml',
    ],
    'assets': {
        'web.assets_backend': [],
    },
    'installable': True,
    'application': True,
}
