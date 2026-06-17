# -*- coding: utf-8 -*-
"""Cleanup hooks for customer_vetting (removed models left in the database)."""

import logging

_logger = logging.getLogger(__name__)

_MODULE_NAME = 'customer_vetting'

# Known removed models (fallback if not listed in ir.model.data anymore).
_KNOWN_REMOVED_MODELS = (
    'service.request.quality',
    'grain.cleaning.stage',
)


def _get_orphan_models(env, module_name):
    """Models referenced by module data but no longer registered in Python."""
    env.cr.execute(
        """
        SELECT DISTINCT model
        FROM ir_model_data
        WHERE module = %s
          AND model IS NOT NULL
          AND model != ''
        """,
        (module_name,),
    )
    from_module_data = {row[0] for row in env.cr.fetchall()}
    from_module_data.update(_KNOWN_REMOVED_MODELS)
    return sorted(m for m in from_module_data if m not in env.registry)


def _cleanup_orphan_model(env, model_name):
    """Remove metadata and tables for a model no longer registered in Python."""
    table = model_name.replace('.', '_')

    env.cr.execute(
        "DELETE FROM ir_model_data WHERE model = %s",
        (model_name,),
    )
    env.cr.execute(
        "DELETE FROM mail_message WHERE model = %s",
        (model_name,),
    )
    env.cr.execute(
        "DELETE FROM mail_followers WHERE res_model = %s",
        (model_name,),
    )
    env.cr.execute(
        "DELETE FROM ir_default WHERE field_id IN "
        "(SELECT id FROM ir_model_fields WHERE model = %s)",
        (model_name,),
    )
    env.cr.execute(
        "DELETE FROM ir_model_access WHERE model_id IN "
        "(SELECT id FROM ir_model WHERE model = %s)",
        (model_name,),
    )
    env.cr.execute(
        "DELETE FROM ir_rule WHERE model_id IN "
        "(SELECT id FROM ir_model WHERE model = %s)",
        (model_name,),
    )

    env.cr.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema()
              AND table_name = %s
        )
        """,
        (table,),
    )
    if env.cr.fetchone()[0]:
        env.cr.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
        _logger.info('Dropped orphan table %s', table)

    IrModelFields = env['ir.model.fields'].sudo()
    fields = IrModelFields.search([('model', '=', model_name)])
    if fields:
        fields.unlink()

    IrModel = env['ir.model'].sudo()
    models = IrModel.search([('model', '=', model_name)])
    if models:
        models.unlink()

    _logger.info('Cleaned orphan model metadata for %s', model_name)


def _cleanup_all_orphan_models(env):
    orphan_models = _get_orphan_models(env, _MODULE_NAME)
    if orphan_models:
        _logger.info(
            'customer_vetting: cleaning orphan models %s',
            orphan_models,
        )
    for model_name in orphan_models:
        _cleanup_orphan_model(env, model_name)
    env.flush_all()


def post_init_hook(env):
    """On install/upgrade, remove DB leftovers from deleted models."""
    _cleanup_all_orphan_models(env)
    orders = env['sale.order'].search([
        ('service_request_id', '!=', False),
        ('state', 'in', ('sale', 'done')),
    ])
    if orders:
        orders._sync_overall_customer_report_lines()


def uninstall_hook(env):
    """Run before module_uninstall to avoid KeyError on removed models."""
    _cleanup_all_orphan_models(env)
