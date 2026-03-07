{
    "name": "Invoice/Bill Approver",
    "version": "1.0",
    "category": "Accounting",
    "author": "Niyat ERP",
    "description": "Module for managing invoice and bill approval with separate groups for each action button.",
    "summary": "Control access to invoice/bill actions through security groups",
    "depends": ["base", "account"],
    "data": [
        "security/security_groups.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False
}

