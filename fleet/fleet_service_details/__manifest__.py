{
    'name': 'Fleet Service Cost Details',
    'version': '1.0',
    'summary': 'Add detailed service cost lines to vehicle service logs.',
    'author': 'Henok Gm',
    'category': 'Human Resources/Fleet',
    'depends': ['fleet', 'uom'],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_vehicle_log_services_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}