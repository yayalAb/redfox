{
    'name': 'Store Transfer',
    'summary': 'manage store transfer',
    'description': 'A module to handle store and purchase requests in Odoo',
    'author': 'Niyat Consultancy',
    'depends': ['base', 'stock', 'store_request'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/store_transfer_request.xml',
        'wizard/avilable_warehouse_list.xml',

    ],
    'assets': {
        'web.assets_backend': [],
    },
    'installable': True,
    'application': True,
}
