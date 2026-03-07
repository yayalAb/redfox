# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import date

class CorporateDashboardExecution(models.AbstractModel):
    _inherit = 'corporate.planning.dashboard'

    def _get_execution_data(self, filters=None):
        filters = filters or {}
        
        pva_data = {
            'activity': {'labels': [], 'plan': [], 'actual': [], 'variance': []},
            'financial': {'labels': [], 'plan': [], 'actual': [], 'variance': []},
            'capex': {'labels': [], 'plan': [], 'actual': [], 'variance': []},
        }

        # Domain
        domain = [('fiscal_year', '=', filters.get('year', str(date.today().year)))]
        if filters.get('quarter'): domain.append(('period_quarter', '=', filters.get('quarter')))
        if filters.get('department_id'): domain.append(('department_id', '=', int(filters.get('department_id'))))

        Analysis = self.env['corporate.plan.actual.analysis']

        def fill(key):
            # Using read_group to sum up values by Item Name
            groups = Analysis.read_group(domain + [('report_type', '=', key)], ['item_name', 'plan_amount', 'actual_amount'], ['item_name'])
            for g in groups:
                pva_data[key]['labels'].append(g['item_name'])
                pva_data[key]['plan'].append(g['plan_amount'])
                pva_data[key]['actual'].append(g['actual_amount'])
                pva_data[key]['variance'].append(g['actual_amount'] - g['plan_amount'])

        fill('activity')
        fill('financial')
        fill('capex')

        return {'pva': pva_data}