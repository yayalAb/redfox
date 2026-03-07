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
            'hr_dashboard/static/src/components/chart_renderer/chart_renderer.js',
            'hr_dashboard/static/src/components/chart_renderer/chart_renderer.xml',
            'hr_dashboard/static/src/components/main_dashboard_js.js',
            'hr_dashboard/static/src/components/dashboard_main_view.xml',

            # 👇 Add these lines for KpiCard
            'hr_dashboard/static/src/components/dashboard_card/dashboard_card.js',
            'hr_dashboard/static/src/components/dashboard_card/dashboard_card.xml',
            'hr_dashboard/static/src/css/custom_styles.css',
        ]
    }

}
