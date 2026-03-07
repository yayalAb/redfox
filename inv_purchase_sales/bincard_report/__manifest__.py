{
    'name': 'Bin Card Report',
    'version': '1.0',
    'summary': 'Generates a Bin Card report for a product from a specific warehouse.',
    'author': 'Your Name',
    'category': 'Inventory/Reporting',
    'depends': ['stock'], # Dependency on the Inventory app
    'data': [
        'security/ir.model.access.csv', # We will create this later
        'wizards/bincard_template_wizard_view.xml',
        'reports/bincard_report.xml',
        'reports/bincard_template_document.xml',
        'views/product_template_view.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}