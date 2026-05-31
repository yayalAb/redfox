# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools import frozendict

# Print menu labels created in data/stock_report_actions.xml
_PICKING_REPORT_PRIORITY = {
    'Internal Transfer': 0,
    'Receipt': 1,
    'Delivery Order': 2,
    'Store Return Attachment': 3,
    'Gate Pass Attachment': 4,
}


def _picking_report_sort_key(action_vals):
    """Show custom picking operation reports before Delivery Slip, Labels, etc."""
    name = action_vals.get('name') or ''
    if name in _PICKING_REPORT_PRIORITY:
        return (0, _PICKING_REPORT_PRIORITY[name])
    return (1, action_vals.get('id', 0))


class IrActions(models.Model):
    _inherit = 'ir.actions.actions'

    def _get_bindings(self, model_name):
        result = super()._get_bindings(model_name)
        if model_name != 'stock.picking':
            return result
        reports = result.get('report')
        if not reports:
            return result
        sorted_reports = tuple(sorted(reports, key=_picking_report_sort_key))
        return frozendict({**dict(result), 'report': sorted_reports})
