{
    'name': 'Purchase Request',
    'depends': ['base', 'purchase', 'purchase_stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_groups.xml',
        'security/security_rules.xml',
        'data/ir_sequence.xml',
        'report/proforma_invoice_report_template.xml',
        'report/purchase_request_report_template.xml',
        'report/direct_purchase_report.xml',
        'report/financial_evaluation_report.xml',
        'views/supplies_menu_views.xml',
        'views/supplies_rfp_views.xml',
        'views/purchase_order_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False
}