{
    'name': 'Manufacturing & Financial Dashboard',
    'version': '18.0.1.1.0',
    'category': 'Inventory/Reporting',
    'summary': 'Executive manufacturing, inventory, procurement and financial intelligence dashboard',
    'description': """
        Advanced ERP Manufacturing & Financial Dashboard for Universal Food Complex PLC.
        Executive KPIs, procurement, production, inventory, delivery, collections and profitability.
    """,
    'author': 'Universal Food Complex PLC',
    'depends': [
        'base',
        'web',
        'purchase',
        'stock',
        'sale',
        'account',
        'mrp',
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'mfg_financial_dashboard/static/src/components/chart_renderer/chart_renderer.js',
            'mfg_financial_dashboard/static/src/components/chart_renderer/chart_renderer.xml',
            'mfg_financial_dashboard/static/src/components/dashboard_card/dashboard_card.js',
            'mfg_financial_dashboard/static/src/components/dashboard_card/dashboard_card.xml',
            'mfg_financial_dashboard/static/src/components/pagination_controls/pagination_controls.js',
            'mfg_financial_dashboard/static/src/components/pagination_controls/pagination_controls.xml',
            'mfg_financial_dashboard/static/src/components/main_dashboard.xml',
            'mfg_financial_dashboard/static/src/components/main_dashboard.js',
            'mfg_financial_dashboard/static/src/css/custom_styles.css',
        ],
    },
}
