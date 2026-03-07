{
    'name': 'Manager Dashboard',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Dashboard for managers to view summaries of requests from their team',
    'description': """
        Manager Dashboard
        =================
        Provides managers with a comprehensive dashboard showing:
        - Store Requests summary
        - Purchase Requests summary
        - Payment Requests summary
        - Leave Requests summary
        - Fleet Requests summary
        
        All data is filtered based on organizational hierarchy - managers can see
        their own requests and all requests from their direct and indirect subordinates.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'hr',
        'web',
        'store_request',
        'VendorBid',
        'payment_request',
        'hr_holidays',
        'fleet_vehicle_log_fuel',
        'hr_job_requisition',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_items.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'manager_dashboard/static/src/components/dashboard_card/dashboard_card.js',
            'manager_dashboard/static/src/components/dashboard_card/dashboard_card.xml',
            'manager_dashboard/static/src/components/chart_renderer/chart_renderer.js',
            'manager_dashboard/static/src/components/chart_renderer/chart_renderer.xml',
            'manager_dashboard/static/src/components/main_dashboard_js.js',
            'manager_dashboard/static/src/components/dashboard_main_view.xml',
            'manager_dashboard/static/src/css/custom_styles.css',
        ]
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
