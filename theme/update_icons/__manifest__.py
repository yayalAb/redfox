{
    'name': 'Niyat base Base',
    'version': '18.0',
    'sequence': 1,
    'summary': 'Niyat ERP  Base',
    'description': """
        This is a base module for  Modules.
            ========================================
    """,
    'category': 'Niyat ERP /Base',
    'website': 'https://www..et/',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'web_editor'],
    'data': [
        'data/company_logo.xml',
        'view/icons_view.xml'
    ],

    'demo': [],
    'post_init_hook': 'update_menu_icons',
    'installable': True,
    'price': 49.99,
    'currency': 'ETB',
    'application': True,
    'auto_install': False,

}
