{
    'name': 'HR Update Views',
    'version': '1.0',
    'category': 'HR Update Views',
    'summary': 'Adds a relationship field for emergency contacts on Employee form, makes the hr employee fields required, creating a pop up message upon successfull creation of employee.',
    'depends': ['hr'],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'assets': {

    },
    'installable': True,
    'application': False,
}
