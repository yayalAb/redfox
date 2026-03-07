# employee_kpi_appraisal/__manifest__.py
{
    'name': 'Employee KPI Appraisal Extension',
    'version': '1.0',
    'summary': 'Adds a custom KPI-based evaluation system to the standard Appraisals app.',
    'description': """
        This module extends the Odoo Appraisals application.
        - Adds a new "KPIs" menu under Configuration to define company, department, or employee-specific KPIs.
        - Adds a new "KPI Evaluations" menu to perform evaluations using the defined KPIs.
    """,
    'author': 'Niyat ERP',
    'category': 'Human Resources/Appraisals',
    'depends': ['hr', 'hr_appraisal', 'project', 'hr_timesheet', 'appraisal_extension'], 
    'data': [
        'security/ir.model.access.csv',
        'views/appraisal_kpi_views.xml',
        'views/employee_evaluation_views.xml',
        'views/employee_appraisal_views.xml',
        'views/kpi_category_views.xml',
        'views/appraisal_menus.xml', 
        'views/project_task_views.xml',
        'views/project_project_views.xml', 
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}