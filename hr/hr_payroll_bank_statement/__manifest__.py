{
    'name': 'Payroll Bank Statement Letter',
    'category': 'Human Resources/Payroll',
    'summary': 'Generate bank statement letters from selected payslips.',
    'depends': [
        'hr_payroll',
        'account',
        'hr_customizations',
        'custom_payslip_reports',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/paper_format.xml',
        'report/payroll_bank_statement_template.xml',
        'report/payroll_bank_report.xml',
        'views/payroll_statement_report_wizard_views.xml',
        'views/hr_payslip_views.xml',
        'views/res_partner_bank.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
