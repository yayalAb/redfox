{
    'name': 'Internal Maintenance',
    'version': '18.0.1.0.0',
    'category': 'Maintenance',
    'description': 'A module for managing internal equipment maintenance requests',
    'author': 'Niyat ERP',
    'depends': ['base', 'maintenance', 'store_request'],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_request_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}