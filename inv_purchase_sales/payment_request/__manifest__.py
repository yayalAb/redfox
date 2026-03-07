{
    "name": "Payment Request",
    "version": "1.0",
    "category": "Purchases",
    "author": "Niyat ERP",
    "description": "Module for managing payment requests.",
    "summary": "Manage payment requests efficiently",
    "depends": ["base", "account", "purchase", 'hr_expense', 'VendorBid'],
    "data": [
        "security/security_groups.xml",
        "data/ir_sequence.xml",
        "report/payment_report.xml",
        "views/hr_expense_views.xml",  
    ],
    "installable": True,
    "application": False
}