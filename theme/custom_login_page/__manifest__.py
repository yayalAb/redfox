{
    'name': 'Niyat ERP Login Page Theme',
    'version': '1.0.3', # Incremented version
    'summary': 'A beautiful, custom login page for Niyat ERP.',
    'author': 'Niyat Consultancy',
    'depends': [
        'web',
    ],
    'data': [
        'views/login_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_login_page/static/src/css/login.css',
            # 'custom_login_page/static/src/js/login.js',
        ],
        'web.assets_frontend': [
            'custom_login_page/static/src/css/login.css',
            'custom_login_page/static/src/js/login.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}