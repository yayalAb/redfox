{
    'name': 'Partner Registration Required Fields',
    'version': '18.0.1.0.1',
    'category': 'Sales/CRM',
    'summary': 'Require Tax ID and Phone on customer and vendor registration',
    'description': """
        Makes Tax ID and Phone mandatory when creating or updating
        top-level customers and vendors (res.partner without a parent company).
    """,
    'author': 'Universal Food Complex PLC',
    'depends': [
        'base',
        'contacts',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
