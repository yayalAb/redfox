{
    'name': 'Form Save & Discard Text Buttons',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'Show Save and Discard as labeled success/danger buttons on form views',
    'description': """
        Replaces the cloud and X icon buttons in the form control panel with
        explicit Save (success) and Discard (danger) text buttons.
    """,
    'author': 'Universal Food Complex PLC',
    'depends': ['web'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'form_save_discard_buttons/static/src/xml/form_status_indicator.xml',
            'form_save_discard_buttons/static/src/xml/form_view_buttons.xml',
            'form_save_discard_buttons/static/src/xml/x2many_dialog_buttons.xml',
            'form_save_discard_buttons/static/src/scss/form_buttons.scss',
        ],
    },
}
