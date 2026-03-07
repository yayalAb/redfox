{
    "name": "Hr Leave Probation Check",
    "category": "Human Resources",
    "author": "Niyat ERP",
    "depends": ['base', 'hr_holidays'],
    "summary": "A module to check probation period before applying for specific leave types.",
    "data": [
        'views/hr_leave_views.xml',
    ],  
    "installable": True,
    "application": False,
    "auto_install": True,
}