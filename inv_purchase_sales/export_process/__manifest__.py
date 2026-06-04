{
    'name': 'Export Process',
    'version': '18.0.1.0.0',
    'summary': 'Export sales workflow from quotation to NBE settlement',
    'description': """
        Manages the export business process: quotation, contract, payment method
        (CAD / LC / TT), parallel shipment documentation and logistics tracks,
        customer payments, and NBE settlement.
    """,
    'author': 'Niyat Consultancy.',
    'category': 'Sales/Sales',
    'depends': ['sale', 'account', 'stock', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/export_process_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
