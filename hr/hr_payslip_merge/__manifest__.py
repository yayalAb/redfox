{
    'name': 'HR Payslip Merge',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Prevent duplicate payslips - generate one payslip per employee using most recent contract',
    'description': """
        This module modifies the payslip batch generation to ensure only one payslip
        is created per employee using the most recent contract, preventing duplicates
        when an employee has multiple contracts in the same period (e.g., promotions).
        
        Features:
        - Automatically uses the most recent contract (by start date) when generating payslips
        - Automatically adds employees to existing payslip batches when a new contract is created
        - Only adds to batches in 'draft' or 'verify' state
        - Uses the most recent contract for payslip calculation
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['hr_payroll'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

