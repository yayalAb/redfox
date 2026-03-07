{
    'name': 'Fleet Contract Expiry Reminder',
    'version': '1.0.0',
    'category': 'Fleet Management',
    'summary': """This module sends reminders for fleet contract expirys.""",
    'description': """
This module helps fleet managers to keep track of contract expirys by sending timely reminders.
""",
    'author': 'Niyat ERP',
    'depends': [
        'fleet',
    ],
    'data': [
        'data/contract_reminder.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
