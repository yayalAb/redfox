{
    'name': 'Supplier Registration',
    'depends': ['base', 'website', 'contacts'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

# 'security/ir.model.access.csv',
# 'security/security_groups.xml',
# 'views/website_views.xml',
# 'views/supplier_registration_portal.xml',
# 'views/email_templates.xml',
# 'wizard/supplies_blacklist_wizard_view.xml',
# 'wizard/supplies_reject_application_wizard_views.xml',

# 'assets': {
#     'web.assets_frontend': [
#         'web/static/lib/jquery/jquery.js',
#         'supplier_registration/static/src/js/registration.js',
#     ],
#     'web.assets_backend': [
#         'supplier_registration/static/src/components/**/*.js',
#         'supplier_registration/static/src/components/**/*.xml',
#         'supplier_registration/static/src/components/**/*.scss',
#     ],
# },
