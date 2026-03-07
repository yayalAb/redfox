from . import models

import base64

from odoo.tools import file_open


def _setup_module(env):
    if env.ref('base.main_company', False):
        with file_open('base/static/img/res_company_logo.png', 'rb') as file:
            env.ref('base.main_company').write({
                'appbar_image': base64.b64encode(file.read())
            })


def uninstalled_clarity_theme(env):
    """remove clarity theme if installed."""
    print("Checking for clarity themes to uninstall...")
    # env = api.Environment(cr, SUPERUSER_ID, {})
    modules = env['ir.module.module'].search(
        [('name', 'in', ['clarity_backend_theme_bits']), ('state', '=', 'installed')])
    if modules:
        [module.sudo().module_uninstall() for module in modules]
