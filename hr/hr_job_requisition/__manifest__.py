{
    'name': 'HR Job Requisition',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_recruitment'],
    'data': [
        'security/users_groups.xml',
        'security/ir.model.access.csv',
        'security/requisition_rules.xml',
        'data/email_templates.xml',
        'views/job_requisition_wizard_views.xml',
        'views/job_requisition_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_job_requisition/static/src/js/recruit_widget.js',
        ]
    },
    'installable': True,
}
