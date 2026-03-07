{
    "name": "Accounting Groups",
    "version": "1.0",
    "category": "Accounting",
    "author": "Niyat ERP",
    "description": "Module for managing different user groups for Journal Entries and Payroll Batches.",
    "summary": "User groups for Journal Entries and Payroll Batches",
    "depends": ["base", 'hr_payroll', 'account'],
    "data": [
        "security/security_groups.xml",
        "views/payslip_batch_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False
}