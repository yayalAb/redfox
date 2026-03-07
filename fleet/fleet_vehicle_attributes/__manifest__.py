{
    'name': 'Fleet Vehicle Attributes',
    'category': 'Human Resources',
    'depends': ['base', 'fleet', 'fleet_vehicle_log_fuel'],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_vehicle_views.xml',
        'views/fleet_deposit_views.xml',
        'views/fleet_vehicle_log_fuel_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': True
}