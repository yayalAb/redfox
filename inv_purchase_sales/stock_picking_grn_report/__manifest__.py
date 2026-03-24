{
    'name': 'Stock Picking GRN Report',
    'summary': 'GRN, delivery note, good receiving note, and get pass attachment PDFs for stock pickings',
    'category': 'Inventory',
    'version': '18.0.1.0.7',
    'depends': [
        'stock',
        'sale_stock',
        'stock_picking_custom',
        'store_request',
    ],
    'data': [
        'report/paper_format.xml',
        'reports/customer_delivery_note_report.xml',
        'reports/customer_good_receiving_note_report.xml',
        'reports/get_pass_attachment_report.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
