# -*- coding: utf-8 -*-
from odoo import models, api, fields
from datetime import date

class CorporateDashboardService(models.AbstractModel):
    _name = 'corporate.planning.dashboard'
    _description = 'Dashboard Data Service'

    @api.model
    def get_dashboard_data(self, filters=None):
        
        filters = filters or {}
        
        # --- 1. PREPARE CONTEXT DATA ---
        selected_comp = int(filters.get('company_id')) if filters.get('company_id') else False
        selected_year = filters.get('year', 'all') # Default to 'all' or current year

        # Fetch Active Strategy to determine valid years
        # We need this here to populate the Year Dropdown
        strategy = self.env['corporate.strategy.document'].search([
            ('state', 'in', ['active', 'draft'])
        ], order='state asc, id desc', limit=1)

        available_years = []
        if strategy and strategy.start_year:
            # FIX: Ensure start_year is treated as an integer before adding i
            try:
                start_int = int(strategy.start_year)
            except ValueError:
                start_int = date.today().year # Fallback if text is garbage

            available_years = [str(start_int + i) for i in range(5)]
        else:
            # Fallback
            curr = date.today().year
            available_years = [str(curr - 1), str(curr), str(curr + 1)]
        # --- 2. CALL SUB-MODULES ---
        data = {
            'cards': {},
            'charts': {'bsc': {}, 'finance': {}, 'pva': {}},
            'card_links': {},
            'strategy_usage': []
        }

        if hasattr(self, '_get_strategy_data'):
            strategy_data = self._get_strategy_data(filters)
            data['cards'].update(strategy_data.get('cards', {}))
            data['charts']['bsc'] = strategy_data.get('bsc_data', {})
            data['charts']['finance'] = strategy_data.get('finance_data', {})
            data['charts']['years'] = strategy_data.get('years', [])
            data['card_links'].update(strategy_data.get('links', {}))
            if 'strategy_usage' in strategy_data:
                data['strategy_usage'] = strategy_data['strategy_usage']

        if hasattr(self, '_get_execution_data'):
            execution_data = self._get_execution_data(filters)
            data['charts']['pva'] = execution_data.get('pva', {})

        # --- 3. PREPARE FILTERS METADATA ---
        
        # LOGIC: Strict Department Filter
        dept_domain = []
        
        # A. Filter by Company (If selected)
        if selected_comp:
            dept_domain.append(('company_id', '=', selected_comp))
            
        # B. Security Filter (If not Manager, only see own hierarchy)
        if not self.env.user.has_group('corporate_planning.group_planning_manager'):
            user_dept = self.env.user.employee_id.department_id
            if user_dept:
                dept_domain.append(('id', 'child_of', user_dept.id))
            else:
                dept_domain.append(('id', '=', -1)) # No access

        data['filters'] = {
            'departments': self.env['hr.department'].search_read(dept_domain, ['id', 'name']),
            'companies': self.env['res.company'].search_read([], ['id', 'name']),
            'available_years': available_years, # <--- NEW LIST FOR DROPDOWN
            'current_year': selected_year,
            'current_quarter': filters.get('quarter', ''),
            'current_dept': int(filters.get('department_id')) if filters.get('department_id') else False,
            'current_comp': selected_comp
        }

        return data