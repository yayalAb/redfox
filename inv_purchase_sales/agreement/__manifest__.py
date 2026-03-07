# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale Agreement",
    "summary": "Adds an agreement object",
    "version": "18.0.1.0.0",
    "category": "Contract",
    "author": "Akretion, "
    "Yves Goldberg (Ygol Internetwork), "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/agreement",
    "license": "AGPL-3",
    "depends": ["mail",'sale'],
    "data": [
        "security/agreement_security.xml",
        "security/ir.model.access.csv",

        "views/agreement.xml",
        "views/agreement_type.xml",
        "views/agreement_menu.xml",
         "views/sale_order.xml",
         'data/ir_cron.xml',
    ],
    "demo": ["demo/demo.xml"],
    "development_status": "Beta",
    "maintainers": [
        "ygol",
        "alexis-via",
    ],
    "installable": True,
}
