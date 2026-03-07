{
    'name': 'Design Process',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Manage the design process in manufacturing',
    'author': 'Niyat ERP',
    'depends': ['base', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/design_actions_views.xml',
        'views/design_wizard_views.xml',
        'views/hv_design_views.xml',
        'views/lv_design_views.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}