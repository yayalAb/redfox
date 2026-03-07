# __manifest__.py
{
    'name': 'Main Dashboard',
    'version': '18.0.1.0.0',
    'category': '',
    'summary': 'Main Dashboard',
    'icon': '/main_dashboard/static/src/description/icon2.png',
    'description': """
        Main  Dashboard.
    """,
    'author': 'Yayal Abayneh',
    'website': 'https://www.yourwebsite.com',
    'depends': ['base', 'sale', 'web'],  # Depends on base and crm modules
    'data': [
        'views/main_dashboard_view.xml',

    ],


    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'main_dashboard/static/src/components/chart_renderer/chart_renderer.js',
            'main_dashboard/static/src/components/chart_renderer/chart_renderer.xml',
            'main_dashboard/static/src/components/main_dashboard_js.js',
            'main_dashboard/static/src/components/dashboard_main_view.xml',

            # 👇 Add these lines for KpiCard
            'main_dashboard/static/src/components/dashboard_card/dashboard_card.js',
            'main_dashboard/static/src/components/dashboard_card/dashboard_card.xml',
            'main_dashboard/static/src/css/custom_styles.css',
        ]
    }

}
