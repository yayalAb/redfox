{
    'name': 'HR Customizations',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Adds a relationship field for emergency contacts on Employee form, makes the hr employee fields required, creating a pop up message upon successfull creation of employee.',
    'depends': ['hr_recruitment', 'hr', 'bus', 'hr_payroll'],
    'data': [
        'data/hr.employee.relationship.csv',
        'security/ir.model.access.csv',
        'data/employee_id_sequence.xml',
        'views/hr_employee_views.xml',
        'views/hr_department_views.xml',
        'views/hr_applicant_views.xml',
        'views/cost_center.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'hr_customizations/static/src/js/email_validation_widget.js',
            'hr_customizations/static/src/js/phone_validation_widget.js',
            'hr_customizations/static/src/js/name_validation_widget.js',
            'hr_customizations/static/src/js/salary_widget.js',
        ],
    },
    'installable': True,
    'application': False,
}
