# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Remove DB metadata for models deleted from customer_vetting source code."""
    if not version:
        return
    from odoo.api import Environment
    from odoo import SUPERUSER_ID

    env = Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.customer_vetting.hooks import _cleanup_all_orphan_models

    _cleanup_all_orphan_models(env)
