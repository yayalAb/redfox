from . import controller, models


def uninstalled_muk_theme(env):
    """remove muk theme if installed."""
    modules = env['ir.module.module'].search([('name', 'in', ['muk_web_chatter',
                                             'muk_web_appsbar', 'muk_web_theme', 'muk_web_dialog']), ('state', '=', 'installed')])
    if modules:
        [module.sudo().module_uninstall() for module in modules]
