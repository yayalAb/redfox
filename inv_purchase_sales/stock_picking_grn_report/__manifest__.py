{
    'name': 'Stock Picking GRN Report',
    'summary': 'Goods Receiving Note PDF report for inventory operations (Red Fox format)',
    'category': 'Inventory',
    'version': '18.0.1.1.0',
    'depends': [
        'stock',
        'stock_picking_custom',
        'store_request',
    ],
    'data': [
        'report/paper_format.xml',
        'reports/goods_receiving_note_report.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
