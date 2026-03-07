# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.tools import float_round, html2plaintext
from datetime import date

class CorporateDashboardStrategy(models.AbstractModel):
    _inherit = 'corporate.planning.dashboard'

    def _get_strategy_data(self, filters=None):
        filters = filters or {}
        
        # --- 1. PARSE FILTERS ---
        # Raw filter value
        selected_year = filters.get('year', 'all')
        
        # Calculated Year for AOP/Operational metrics
        # If user selects "All Years", we default Operational metrics to THIS year
        # because AOPs are strictly yearly.
        if selected_year.isdigit():
            current_year = selected_year
        else:
            current_year = str(date.today().year)

        dept_id = int(filters.get('department_id')) if filters.get('department_id') else False
        comp_id = int(filters.get('company_id')) if filters.get('company_id') else False

        # --- 2. FETCH ACTIVE STRATEGY ---
        strategy_domain = [('state', 'in', ['active', 'draft'])]
        if comp_id:
            strategy_domain.append(('company_id', '=', comp_id))
            
        strategy = self.env['corporate.strategy.document'].search(strategy_domain, order='state asc, id desc', limit=1)

        # --- 3. IDENTITY DATA ---
        identity_data = {
            'vision': "No Strategy Document Found",
            'mission': "No Strategy Document Found",
            'values': []
        }

        if strategy:
            vision_txt = html2plaintext(strategy.vision) if strategy.vision else "No Vision Defined"
            mission_txt = html2plaintext(strategy.mission) if strategy.mission else "No Mission Defined"
            identity_data = {
                'vision': vision_txt,
                'mission': mission_txt,
                'values': [{'name': v.name, 'desc': v.description} for v in strategy.core_value_ids]
            }

        # --- 4. STRATEGIC FINANCIALS (Forecast) ---
        strat_rev = 0.0
        strat_exp = 0.0
        
        if strategy:
            rev_lines = strategy.revenue_forecast_ids
            exp_lines = strategy.expense_forecast_ids
            
            # Filter by Company
            if comp_id:
                rev_lines = rev_lines.filtered(lambda r: r.business_unit_id.id == comp_id)
                exp_lines = exp_lines.filtered(lambda e: e.business_unit_id.id == comp_id)

            if selected_year == 'all':
                # Sum ALL columns (Y1 to Y5)
                for line in rev_lines:
                    strat_rev += (line.y1_value + line.y2_value + line.y3_value + line.y4_value + line.y5_value)
                for line in exp_lines:
                    strat_exp += (line.y1_value + line.y2_value + line.y3_value + line.y4_value + line.y5_value)
            else:
                # Specific Year Logic
                try:
                    target_year_int = int(selected_year)
                    if strategy.start_year:
                        try:
                            start_year_int = int(strategy.start_year)
                        except ValueError:
                            start_year_int = date.today().year
                    else:
                        start_year_int = date.today().year

                    year_offset = target_year_int - start_year_int + 1
                    
                    if 1 <= year_offset <= 5:
                        col_name = f'y{year_offset}_value'
                        strat_rev = sum(rev_lines.mapped(col_name))
                        strat_exp = sum(exp_lines.mapped(col_name))
                except (ValueError, TypeError):
                    pass 

        strat_profit = strat_rev - strat_exp

        # --- 5. ANNUAL OPERATING PLAN (AOP) METRICS ---
        # Note: Uses 'current_year' variable defined at the top
        
        # A. AOP Financial Breakdown
        fin_aop_domain = [
            ('plan_id.fiscal_year', '=', current_year),
            ('plan_id.state', '=', 'approved')
        ]
        if comp_id: fin_aop_domain.append(('plan_id.company_id', '=', comp_id))
        if dept_id: fin_aop_domain.append(('plan_id.department_id', '=', dept_id))

        fin_lines = self.env['corporate.operating.financial'].search(fin_aop_domain)
        
        aop_revenue = sum(fin_lines.filtered(lambda l: l.category == 'revenue').mapped('annual_budget'))
        aop_cos = sum(fin_lines.filtered(lambda l: l.category == 'cos').mapped('annual_budget'))
        aop_opex = sum(fin_lines.filtered(lambda l: l.category == 'opex').mapped('annual_budget'))
        aop_other = sum(fin_lines.filtered(lambda l: l.category == 'other').mapped('annual_budget'))

        capex_lines = self.env['corporate.operating.capex'].search(fin_aop_domain)
        aop_capex = sum(capex_lines.mapped('annual_budget_etb'))

        # B. Budget Utilization (Accounting Link)
        t_bud = 0.0
        t_commit = 0.0
        has_budget = False
        target_budget_ids = []

        start_of_year = f'{current_year}-01-01'
        end_of_year = f'{current_year}-12-31'
        
        aop_budget_domain = [
            ('budget_id', '!=', False),
            ('start_date', '<=', end_of_year),
            ('end_date', '>=', start_of_year),
        ]
        if dept_id: aop_budget_domain.append(('department_id', '=', dept_id))
        if comp_id: aop_budget_domain.append(('company_id', '=', comp_id))
            
        relevant_plans = self.env['corporate.planning.annual.plan'].search(aop_budget_domain)
        linked_budgets = relevant_plans.mapped('budget_id')
        
        if linked_budgets:
            has_budget = True
            target_budget_ids = linked_budgets.ids
            
            budget_model = 'budget.line' if 'budget.line' in self.env else 'crossovered.budget.lines'
            if budget_model in self.env:
                link_field = 'budget_analytic_id' if 'budget_analytic_id' in self.env[budget_model]._fields else 'crossovered_budget_id'
                amount_field = 'budget_amount' if 'budget_amount' in self.env[budget_model]._fields else 'planned_amount'
                commit_field = 'committed_amount' if 'committed_amount' in self.env[budget_model]._fields else 'practical_amount'

                budget_lines = self.env[budget_model].search([(link_field, 'in', linked_budgets.ids)])
                t_bud = sum(budget_lines.mapped(amount_field))
                t_commit = sum(budget_lines.mapped(commit_field))
                if t_commit < 0: t_commit = abs(t_commit)

        utilization = (t_commit / t_bud * 100) if t_bud > 0 else 0.0

        # --- 6. GENERAL METRICS ---
        
        # Risk
        risk_domain = [('risk_level', 'in', ['critical', 'significant']), ('state', 'in', ['draft', 'active'])]
        if dept_id: risk_domain.append(('department_id', '=', dept_id))
        if comp_id: risk_domain.append(('company_id', '=', comp_id))
        risk_count = self.env['corporate.risk.register'].search_count(risk_domain)
        
        # Projects
        proj_domain = []
        if comp_id: proj_domain.append(('company_id', '=', comp_id))
        project_count = self.env['project.project'].search_count(proj_domain)

        # Avg Performance (Activity Plan vs Actual)
        # Using 'current_year' here, fixing the NameError
        plan_domain = [('plan_id.state', '=', 'approved'), ('plan_id.fiscal_year', '=', current_year)]
        if dept_id: plan_domain.append(('plan_id.department_id', '=', dept_id))
        if comp_id: plan_domain.append(('plan_id.company_id', '=', comp_id))
        
        plan_lines = self.env['corporate.operating.activity'].search(plan_domain)
        
        actual_domain = [('fiscal_year', '=', current_year)]
        if dept_id: actual_domain.append(('department_id', '=', dept_id))
        if comp_id: actual_domain.append(('company_id', '=', comp_id))
        
        actual_groups = self.env['corporate.execution.activity'].read_group(actual_domain, ['activity_master_id', 'actual_qty'], ['activity_master_id'])
        actual_map = {g['activity_master_id'][0]: g['actual_qty'] for g in actual_groups if g['activity_master_id']}

        total_pct = 0.0
        count = 0
        for line in plan_lines:
            target = line.annual_target
            if target > 0:
                actual = actual_map.get(line.activity_master_id.id, 0.0)
                pct = (actual / target) * 100
                if pct > 100: pct = 100
                total_pct += pct
                count += 1
        avg_performance = (total_pct / count) if count > 0 else 0.0

        # --- 7. LINKS & CHARTS DATA ---
        view_values = self.env.ref('odoo_corporate_planning.view_strategy_doc_form_values', False)
        view_pillars = self.env.ref('odoo_corporate_planning.view_strategy_doc_form_pillars', False)
        view_goals = self.env.ref('odoo_corporate_planning.view_strategy_doc_form_goals', False)

        bsc_data = {'financial': {'datasets': []}, 'customer': {'datasets': []}, 'process': {'datasets': []}, 'learning': {'datasets': []}}
        finance_data = {'revenue': [], 'expense': [], 'profit': []}
        
        # BSC Logic
        # if strategy:
        #     persp_map = {'financial': ['Financial'], 'customer': ['Customer'], 'process': ['Internal'], 'learning': ['Learning']}
        #     for key, terms in persp_map.items():
        #         lines = strategy.bsc_impl_ids.filtered(lambda l: l.row_type == 'data')
        #         matching = lines.filtered(lambda l: (l.bsc_perspective_id and any(t in l.bsc_perspective_id.name for t in terms)) or (l.perspective and hasattr(l.perspective, 'name') and any(t in l.perspective.name for t in terms)))
                
        #         goals = []
        #         if 'strategy_goal_id' in self.env['corporate.strategy.bsc.impl']._fields:
        #             goals = list(set(matching.mapped('strategy_goal_id.name')))
        #         else:
        #             goals = list(set(matching.mapped('goal_id.name')))
                
        #         for g in filter(None, goals):
        #             if 'strategy_goal_id' in self.env['corporate.strategy.bsc.impl']._fields:
        #                 glines = matching.filtered(lambda l: l.strategy_goal_id.name == g)
        #             else:
        #                 glines = matching.filtered(lambda l: l.goal_id.name == g)
        #             y_vals = [sum(glines.mapped(f'y{i}_target')) for i in range(1,6)]
        #             bsc_data[key]['datasets'].append({'label': g, 'data': y_vals, 'tension': 0.3})

        # Financial Chart Logic
        all_f = strategy.revenue_forecast_ids | strategy.expense_forecast_ids
        companies = all_f.mapped('business_unit_id')
        if comp_id:
            companies = companies.filtered(lambda c: c.id == comp_id)

        for comp in companies:
            revs = strategy.revenue_forecast_ids.filtered(lambda r: r.business_unit_id == comp)
            exps = strategy.expense_forecast_ids.filtered(lambda r: r.business_unit_id == comp)
            r_v = [sum(revs.mapped(f'y{i}_value')) for i in range(1,6)]
            e_v = [sum(exps.mapped(f'y{i}_value')) for i in range(1,6)]
            p_v = [r - e for r, e in zip(r_v, e_v)]
            finance_data['revenue'].append({'label': comp.name, 'data': r_v})
            finance_data['expense'].append({'label': comp.name, 'data': e_v})
            finance_data['profit'].append({'label': comp.name, 'data': p_v})
        
        # Strategy Usage Table
        strategy_usage = []
        u_domain = [('strategy_type_id', '!=', False)]
        if dept_id: u_domain.append(('department_id', '=', dept_id))
        annual_plans = self.env['corporate.planning.annual.plan'].search_read(u_domain, ['department_id', 'name', 'strategy_type_id', 'start_date'])
        for plan in annual_plans:
            strategy_usage.append({
                'department': plan['department_id'][1] if plan['department_id'] else 'Unknown',
                'plan_name': plan['name'],
                'strategy': plan['strategy_type_id'][1],
                'year': str(plan['start_date'])[:4]
            })

        return {
            'cards': {
                'doc_name': strategy.name if strategy else "No Strategy",
                'identity': identity_data,
                'strat_rev': strat_rev,
                'strat_exp': strat_exp,
                'strat_profit': strat_profit,
                'aop_revenue': aop_revenue,
                'aop_cos': aop_cos,
                'aop_opex': aop_opex,
                'aop_other': aop_other,
                'aop_capex': aop_capex,
                'risk_count': risk_count,
                'active_projects': project_count,
                'avg_performance': float_round(avg_performance, precision_digits=1),
                'budget_utilization': float_round(utilization, precision_digits=1),
                'has_budget': has_budget,
            },
            'links': {
                'strategy_id': strategy.id if strategy else False,
                'view_values_id': view_values.id if view_values else False,
                'view_pillars_id': view_pillars.id if view_pillars else False,
                'view_goals_id': view_goals.id if view_goals else False,
                'budget_ids': target_budget_ids,
            },
            'bsc_data': bsc_data,
            'finance_data': finance_data,
            'years': ['Y1', 'Y2', 'Y3', 'Y4', 'Y5'],
            'strategy_usage': strategy_usage
        }