{
    'name': 'Inventory Validations',
    'version': '1.0.0',
    'author': 'Niyat ERP',
    'category': 'Inventory/Inventory',
    'summary': 'Adds various validation constraints to inventory-related models.',
    'description': """
This module centralizes all custom validation logic for inventory, sales,
and purchase operations to ensure data integrity.

Validations added:
- Prevents negative Sales Price on products.
- Prevents negative Cost on products.
- Prevents negative Quantity on stock moves.
    """,
    'depends': [
        'product',
        'stock',
        'sale',
        'purchase'
    ],
    'data': [],
    'installable': True,
    'application': False
}