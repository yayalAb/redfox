{
    'name': 'HR Employee Back Payment',
    'version': '1.0.0',
    'summary': 'Manage and process employee salary arrears by integrating with regular payslips.',
    'author': 'Niyat ERP',
    'category': 'Human Resources/Payroll',
    'depends': ['hr_payroll', 'hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/hr_back_payment_data.xml',
        'views/back_payment_views.xml',
        'views/hr_payslip_run_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}