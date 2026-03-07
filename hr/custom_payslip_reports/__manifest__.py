{
    'name': 'Custom Payslip PDF Reports',
    'version': '1.0',
    'summary': 'Generate multiple custom PDF payslip reports',
    'author': 'Niyat ERP',
    'depends':[
        'hr_payroll',
        'hr_customizations',
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_view.xml',
        'views/payslip_report_wizard_view.xml',
        'views/social_contribution_wizard_view.xml',
        'report/paper_format.xml',
        'report/report_actions.xml',
        'report/report_templates.xml',
    ],
    'installable': True,
    'application': False,
}