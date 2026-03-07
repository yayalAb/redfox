from . import models


def uninstalled_clarity_theme(env):
    """remove clarity theme if installed."""
    print("Checking for clarity themes to uninstall...")
    # env = api.Environment(cr, SUPERUSER_ID, {})
    modules = env['ir.module.module'].search(
        [('name', 'in', ['clarity_backend_theme_bits']), ('state', '=', 'installed')])
    if modules:
        [module.sudo().module_uninstall() for module in modules]
