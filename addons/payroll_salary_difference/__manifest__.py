# -*- coding: utf-8 -*-
{
    "name": "Payroll Salary Difference",
    "version": "18.0.1.0.0",
    "category": "Human Resources/Payroll",
    "summary": "Compare salary differences between two payroll batches",
    "description": """
        This module allows you to compare salary differences between two payroll batches.
        It displays employees as rows and salary rules as columns, showing the difference
        between batch1 and batch2. By default, it uses the two most recent batches.
    """,
    "author": "Niyat ERP",
    "depends": ["hr_payroll"],
    "data": [
        "security/ir.model.access.csv",
        "views/payroll_difference_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "payroll_salary_difference/static/src/components/payroll_difference_table_main.js",
            "payroll_salary_difference/static/src/components/payroll_difference_table_main.xml",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}

