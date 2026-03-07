{
    'name': 'Customer Vetting Workflow',
    'version': '1.0',
    'summary': 'Implements a vetting and approval workflow for customers.',
    'author': 'Henok Gm',
    'category': 'Sales/CRM',
    'depends': [
        'base',
        'contacts',
        'sale_management',
    ],
    'data': [
        'security/customer_vetting_groups.xml',
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': True,
}