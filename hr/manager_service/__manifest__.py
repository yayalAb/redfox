{
    'name': 'HR Manager Service',
    'version': '1.0',
    'summary': 'Module for managing services related to Department Heads',   
    'category': 'Human Resources',
    'author': 'Niyat ERP',
    'license': 'AGPL-3',
    'depends': ['hr', 'mail', 'stock', 'project', 'hr_holidays', 'hr_employee_self_service', 'store_request', 'training_requisition', 'hr_job_requisition'],
    'data': [
        'security/security_groups.xml',
        'views/manager_service_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,

}