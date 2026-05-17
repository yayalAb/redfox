{
    'name': 'Customer Vetting Workflow',
    'version': '1.0',
    'summary': 'Implements a vetting and approval workflow for customers.',
    'author': 'Henok Gm',
    'category': 'Sales/CRM',
    'depends': [
        'base',
        'contacts',
        'mail',
        'product',
        'sale_management',
    ],
    'data': [
        'security/customer_vetting_groups.xml',
        'security/ir.model.access.csv',
        'data/service_request_sequence.xml',
        'views/service_request_views.xml',
        'views/sale_order_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': True,
}
