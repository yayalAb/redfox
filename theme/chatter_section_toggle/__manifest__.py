
{
    'name': 'Show/Hide Chatter',
    'version': '1.2',
    'sequence': 10,
    'author': "JD DEVS",
    'depends': ['base', 'base_setup', 'web', 'web_tour'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            "chatter_section_toggle/static/src/css/chatter.css",
            "chatter_section_toggle/static/src/js/form.js",

        ],
    },
    "images": [
        "static/description/banner.png"
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
