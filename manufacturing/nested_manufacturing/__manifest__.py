{
    'name': 'Nested Manufacturing',
    'descritption': 'using workorders as nested manufacturing worder',
    'author': 'Niyat ERP',
    'depends': ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
        # 'views/mrp_routing_workcenter_views.xml',
        'views/production_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}