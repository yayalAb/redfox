{
    'name': 'CRM Customization',
    'version': '1.0',
    'summary': 'Adds a source field to the CRM form.',
    'author': 'Henok Gm',
    'depends': [
        'crm',
        'sale_management',
        'agreement',
        'crm_iap_mine', 
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/crm_lead_view.xml',
        'views/crm_sector_views.xml', #added sector and industry views
        'views/crm_social_message_view.xml',
        'views/social_media_lead_view.xml',
        'views/crm_facebook_post_view.xml',
        'views/crm_lead_hide_generate_leads.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
