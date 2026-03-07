{
    'name': 'Client Maintenance',
    'version': '18.0.1.0.0',
    'category': 'Manufacturing',
    'description': 'A module for managing maintenance requests from clients',
    'author': 'Niyat ERP',
    'depends': ['base', 'mrp', 'project', 'design_process', 'nested_manufacturing'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/client_maintenance_wizard_views.xml',
        'views/service_request_views.xml',
        'views/measurement_log_views.xml',
        'views/service_type_views.xml',
        'views/fault_category_views.xml',
        'views/mrp_production_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}