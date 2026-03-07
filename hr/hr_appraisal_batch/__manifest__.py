{
    'name': "Appraisal Batch",
    'author': 'Niyat ERP',
    'category': 'Human Resources/Appraisals',
    'summary': 'A module to generate a batch of employee evaluation',
    'depends': ['hr_kpi_appraisal'],
    'data': [
        'security/ir.model.access.csv',
        'views/evaluation_batch_wizard_view.xml',
        'views/evaluation_batch_view.xml',
        'views/employee_evaluation_views_inherit.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False
}