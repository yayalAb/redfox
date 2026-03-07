# -*- coding: utf-8 -*-
{
    'name': "VendorBid",
    'summary': "Register vendors, Create & Manage RFPs, Manage RFQ submitted by vendors",
    'description': """
        This module is designed to efficiently manage suppliers and Requests for Proposals (RFPs).
        It allows users to create and manage RFPs, invite suppliers to submit bids, and evaluate the responses.
        The system facilitates the selection of suppliers, negotiation, and finalizing contracts, streamlining the procurement process.
    """,
    'author': "BJIT Limited",
    'category': 'Purchases',
    'version': '0.1',
    'depends': ['purchase', 'website', 'contacts', 'update_menus', 'store_request'],
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'website': "https://bjitgroup.com",
    'application': True,


    # always loaded
    'data': [
        'security/security_groups.xml',
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'report/direct_purchase_report.xml',
        'report/financial_evaluation_report.xml',
        'report/proforma_invoice_report_template.xml',
        'report/purchase_request_report_template.xml',
        'report/purchase_order_report_template.xml',
        'report/paper_format.xml',
        'views/supplies_rfp_views.xml',
        'views/ir_sequence.xml',
        'views/purchase_order_views.xml',
        'views/store_request_inherit_view.xml',
        'views/res_config_settings_views.xml',
        'views/rfp_split_wizard_views.xml',
        'views/committee_member_reject_wizard.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'web/static/lib/jquery/jquery.js',
            'VendorBid/static/src/js/registration.js',
        ],
        'web.assets_backend': [
            'VendorBid/static/src/components/**/*.js',
            'VendorBid/static/src/components/**/*.xml',
            'VendorBid/static/src/components/**/*.scss',
        ],
    },
}
