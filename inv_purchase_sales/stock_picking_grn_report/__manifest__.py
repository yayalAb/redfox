{
    'name': 'Stock Picking GRN Report',
    'summary': 'Goods receiving and customer delivery note PDF reports for stock pickings',
    'category': 'Inventory',
    'version': '18.0.1.0.2',
    'depends': [
        'stock',
        'stock_picking_custom',
        'store_request',
    ],
    'data': [
        'report/paper_format.xml',
        'reports/customer_delivery_note_report.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
