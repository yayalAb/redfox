# custom_stock_reports/__manifest__.py
{
    'name': 'Stock Picking Custom',
    'summary': 'Customizes the Delivery Slips and Receipts to match company format.',
    'category': 'Inventory',
    'depends': [
        'stock',
        'store_request',
    ],
    'data': [
        'reports/picking_operations_template.xml',
        'reports/report_deliveryslip.xml',
        'views/stock_picking_view.xml',
        'views/maintenance_equipment_view.xml',
        'views/store_request_view.xml',
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}