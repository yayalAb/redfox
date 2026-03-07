{
    'name': "Time Off Planning",
    'summary': "Custom module for employees to plan and request time off",
    'description': """
        Allows employees to create yearly time-off plans with start and end dates,
        and request time-offs linked to these plans via a smart button.
    """,
    'author': "Your Name",
    'version': '1.0',
    'depends': ['hr_holidays','hr_employee_self_service'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_timeoff_plan_views.xml',
    ],
    'installable': True,
    'application': False,
}