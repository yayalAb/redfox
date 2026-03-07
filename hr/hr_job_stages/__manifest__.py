{
    'name': 'Hr Job Stages',
    'category': 'Human Resources',
    'summary': 'A module to move multiple applicant from one stage to another stage at once',
    'depends': [
        'hr_recruitment', 'portal_job_posts', 
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_job_wizard_view.xml',
        'views/hr_job_list_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}