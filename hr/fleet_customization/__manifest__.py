{
    'name': 'fleet_customization',
    'version': '1.0',
    'author': 'Niyat ERP',
    'summary': 'Fleet Customization',
    'depends': [
        'base',
        'fleet',
        'fleet_vehicle_attributes',
    ],
    'data': [
        'views/fleet_vehicle_log_contract_views.xml',
        'views/fleet_vehicle_views.xml',
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}