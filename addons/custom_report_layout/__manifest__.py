# my_custom_reports/__manifest__.py
{
    'name': 'Custom Report Layouts',
    'depends': [
        'base',
        'web',
    ],
    'data': [
        'data/sequence.xml',
        'views/report_templates.xml',
        'views/res_config_settings_view.xml',
    ],

    'assets': {
        'web.report_assets_common': [
            'custom_report_layout/static/src/css/fonts.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
