from odoo import api, SUPERUSER_ID


def update_menu_icons(cr, registry):
    """Update menu icons only if the module is installed."""
    from odoo.api import Environment

    env = Environment(cr, SUPERUSER_ID)

    # Check if the hotel_management_odoo module is installed
    module_installed = env["ir.module.module"].search([
        ("name", "=", "hotel_management_odoo"),
        ("state", "=", "installed")
    ])

    if module_installed:
        menu = env.ref(
            "hotel_management_odoo.hotel_management_menu_root", raise_if_not_found=False)
        if menu:
            menu.write(
                {"web_icon": "ashewa_icons,static/src/img/icons/hotel.png"})
