{
    'name': 'Export Process',
    'version': '18.0.2.0.6',
    'summary': 'Export management with Odoo business objects and Kanban workflow',
    'description': """
        Export management system integrated with Sales, Accounting, and Inventory.

        Master model export.export.order drives stages from quotation through NBE settlement.
        Child models handle contract, approvals, LC/CAD/TT, shipping, booking, documents,
        and settlement. Foreign quotations only.
    """,
    'author': 'Niyat Consultancy.',
    'category': 'Sales/Sales',
    'depends': ['sale', 'sale_stock', 'account', 'stock', 'mail', 'stock_picking_custom'],
    'data': [
        'data/cleanup_legacy.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/mail_template.xml',
        'views/export_order_views.xml',
        'views/export_child_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
