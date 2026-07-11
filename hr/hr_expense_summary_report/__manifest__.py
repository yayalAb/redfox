{
    "name": "Expense Payment Request Summary",
    "version": "1.0",
    "category": "Human Resources/Expenses",
    "author": "Niyat ERP",
    "summary": "Print selected employee expenses as a Payment Request Summary Sheet",
    "description": "Generates a PDF summary sheet from selected hr.expense records.",
    "depends": ["hr_expense"],
    "data": [
        "report/payment_request_summary_report.xml",
        "views/hr_expense_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
