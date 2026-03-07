{
    'name': 'Hr Generate Payslip Report PDF',
    'category': 'Human Resources',
    'depends': ['hr_contract', 'hr', 'hr_payroll', 'hr_contract_customization', 'ent_ohrms_loan', 'hr_overtime'],
    'data': [
        'report/payslip_summary_report.xml',
        'views/hr_payslip_views.xml',
        # 'views/payslip_report_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
