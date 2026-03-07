# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MRP II',
    'version': '1.0',
    'category': 'Manufacturing/Manufacturing',
    'sequence': 51,
    'summary': """Work Orders, Planning, Stock Reports.""",
    'depends': ['quality', 'mrp', 'quality_mrp', 'barcodes', 'web_gantt', 'web_tour', 'hr_hourly_cost'],
    'data': [
        'security/ir.model.access.csv',
        'security/mrp_workorder_security.xml',
        'data/mrp_workorder_data.xml',
        'views/hr_employee_views.xml',
        'views/quality_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_workorder_views.xml',
        'views/mrp_operation_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/stock_picking_type_views.xml',
        # 'views/res_config_settings_view.xml',
        # 'views/mrp_workorder_views_menus.xml',
        'wizard/additional_workorder_views.xml',
        'wizard/propose_change_views.xml',
    ],
    'demo': [
        'data/mrp_production_demo.xml',
        'data/mrp_workorder_demo.xml',
        'data/mrp_workorder_demo_stool.xml'
    ],
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'custom_mrp_workorder/static/src/**/*.scss',
            'custom_mrp_workorder/static/src/**/*.js',
            'custom_mrp_workorder/static/src/**/*.xml',
            ('remove', 'custom_mrp_workorder/static/src/mrp_workorder_gantt_*'),
        ],
        'web.assets_backend_lazy': [
            'custom_mrp_workorder/static/src/mrp_workorder_gantt_*',
        ],
        'web.assets_tests': [
            'custom_mrp_workorder/static/tests/tours/**/*',
        ],
        'web.assets_unit_tests': [
            'custom_mrp_workorder/static/tests/**/*',
            ('remove', 'custom_mrp_workorder/static/tests/tours/**/*'),
        ],
    },
    'auto_install': False
}
