{
    'name': 'Portal Job Posts',
    'category': 'Human Resources',
    'summary': 'Edit job positions details in the customer portal.',
    'depends': [
        'website',
        'portal',
        'hr_recruitment',
        'website_hr_recruitment',
    ],
    'data': [
        'views/portal_job_detail.xml',
        'views/portal_jobs_list.xml',
        'views/portal_job_form.xml',
        'views/hr_applicant_view.xml',
        'views/hr_job_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
