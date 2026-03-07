{
    'name': 'Foreign Purchase Project',
    'version': '1.0',
    'summary': 'Module to manage foreign purchase projects',
    'description': '''This module extends the project management features to support foreign purchase projects, including project stages and task types specific to foreign purchases.''',
    'author': 'Niyat ERP',
    'category': 'Project',
    'depends': ['base', 'project', 'purchase', 'project_purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_stage_views.xml',
        'views/project_landed_cost_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
