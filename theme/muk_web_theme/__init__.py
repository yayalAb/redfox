from . import models

import base64

from odoo.tools import file_open


def _setup_module(env):
    if env.ref('base.main_company', False):
        with file_open('web/static/img/favicon.ico', 'rb') as file:
            env.ref('base.main_company').write({
                'favicon': base64.b64encode(file.read())
            })
        with file_open('muk_web_theme/static/src/img/background.png', 'rb') as file:
            env.ref('base.main_company').write({
                'background_image': base64.b64encode(file.read())
            })


def _uninstall_cleanup(env):
    env['res.config.settings']._reset_theme_color_assets()


def uninstalled_clarity_theme(env):
    """remove clarity theme if installed."""
    modules = env['ir.module.module'].search(
        [('name', 'in', ['clarity_backend_theme_bits']), ('state', '=', 'installed')])
    if modules:
        [module.sudo().module_uninstall() for module in modules]
