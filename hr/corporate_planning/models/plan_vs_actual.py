# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

class CorporatePlanVsActual(models.Model):
    _name = 'corporate.plan.actual.analysis'
    _description = 'Plan Vs Actual Analysis'
    _auto = False # SQL View
    _order = 'fiscal_year desc, period_month asc'

    # --- DIMENSIONS ---
    report_type = fields.Selection([
        ('activity', 'Activity'),
        ('financial', 'Financial'),
        ('capex', 'Capex')
    ], string='Report Type', readonly=True)

    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    
    # We use a char field for Item Name to merge Activity/Financial/Capex names into one column
    item_name = fields.Char(string='Item / Activity', readonly=True)
    
    # Financial Specific
    financial_category = fields.Selection([
        ('revenue', 'Revenue'),
        ('cos', 'Cost of Sales'),
        ('opex', 'Opex'),
        ('other', 'Other')
    ], string='Fin. Category', readonly=True)

    # --- TIME ---
    fiscal_year = fields.Char(string='Fiscal Year', readonly=True)
    period_month = fields.Integer(string='Month', readonly=True)
    period_quarter = fields.Selection([
        ('q1', 'Q1'), ('q2', 'Q2'), ('q3', 'Q3'), ('q4', 'Q4')
    ], string='Quarter', readonly=True)

    # --- METRICS ---
    plan_amount = fields.Float(string='Plan', readonly=True)
    actual_amount = fields.Float(string='Actual', readonly=True)
    
    # Computed in Python because SQL math in views can be tricky for aggregates
    variance = fields.Float(string='Variance', readonly=True) 
    achievement_percent = fields.Float(string='% Achieved', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                
                /* =============================================
                   1. ACTIVITY: PLAN vs ACTUAL
                   ============================================= */
                SELECT
                    row_number() OVER () as id,
                    'activity' as report_type,
                    sub.department_id,
                    sub.company_id,
                    sub.item_name,
                    NULL as financial_category,
                    sub.fiscal_year,
                    sub.period_month,
                    sub.period_quarter,
                    sub.plan_amount,
                    sub.actual_amount,
                    (sub.actual_amount - sub.plan_amount) as variance,
                    CASE WHEN sub.plan_amount > 0 THEN (sub.actual_amount / sub.plan_amount) * 100 ELSE 0 END as achievement_percent
                FROM (
                    -- A. ACTIVITY PLAN (Unpivoted)
                    -- We extract m1, m2... and assign them to month 1, 2...
                    SELECT 
                        pl.department_id,
                        pl.company_id,
                        m.name as item_name,
                        pl.fiscal_year,
                        month_series.m as period_month,
                        CASE 
                            WHEN month_series.m BETWEEN 1 AND 3 THEN 'q1'
                            WHEN month_series.m BETWEEN 4 AND 6 THEN 'q2'
                            WHEN month_series.m BETWEEN 7 AND 9 THEN 'q3'
                            ELSE 'q4' 
                        END as period_quarter,
                        CASE 
                            WHEN month_series.m = 1 THEN l.m1
                            WHEN month_series.m = 2 THEN l.m2
                            WHEN month_series.m = 3 THEN l.m3
                            WHEN month_series.m = 4 THEN l.m4
                            WHEN month_series.m = 5 THEN l.m5
                            WHEN month_series.m = 6 THEN l.m6
                            WHEN month_series.m = 7 THEN l.m7
                            WHEN month_series.m = 8 THEN l.m8
                            WHEN month_series.m = 9 THEN l.m9
                            WHEN month_series.m = 10 THEN l.m10
                            WHEN month_series.m = 11 THEN l.m11
                            WHEN month_series.m = 12 THEN l.m12
                        END as plan_amount,
                        0 as actual_amount
                    FROM corporate_operating_activity l
                    JOIN corporate_operating_plan pl ON l.plan_id = pl.id
                    JOIN corporate_activity_master m ON l.activity_master_id = m.id
                    CROSS JOIN generate_series(1,12) as month_series(m)
                    WHERE pl.state = 'approved'

                    UNION ALL

                    -- B. ACTIVITY ACTUALS
                    SELECT 
                        e.department_id,
                        e.company_id,
                        m.name as item_name,
                        e.fiscal_year,
                        e.period_month,
                        e.period_quarter,
                        0 as plan_amount,
                        e.actual_qty as actual_amount
                    FROM corporate_execution_activity e
                    JOIN corporate_activity_master m ON e.activity_master_id = m.id
                ) as sub

                UNION ALL

                /* =============================================
                   2. FINANCIAL: PLAN vs ACTUAL
                   ============================================= */
                SELECT
                    row_number() OVER () + 1000000 as id,
                    'financial' as report_type,
                    sub_f.department_id,
                    sub_f.company_id,
                    sub_f.item_name,
                    sub_f.financial_category,
                    sub_f.fiscal_year,
                    sub_f.period_month,
                    sub_f.period_quarter,
                    sub_f.plan_amount,
                    sub_f.actual_amount,
                    (sub_f.actual_amount - sub_f.plan_amount) as variance,
                    CASE WHEN sub_f.plan_amount > 0 THEN (sub_f.actual_amount / sub_f.plan_amount) * 100 ELSE 0 END as achievement_percent
                FROM (
                    -- A. FINANCIAL PLAN
                    SELECT 
                        pl.department_id,
                        pl.company_id,
                        i.name as item_name,
                        l.category as financial_category,
                        pl.fiscal_year,
                        month_series.m as period_month,
                        CASE 
                            WHEN month_series.m BETWEEN 1 AND 3 THEN 'q1'
                            WHEN month_series.m BETWEEN 4 AND 6 THEN 'q2'
                            WHEN month_series.m BETWEEN 7 AND 9 THEN 'q3'
                            ELSE 'q4' 
                        END as period_quarter,
                        CASE 
                            WHEN month_series.m = 1 THEN l.m1
                            WHEN month_series.m = 2 THEN l.m2
                            WHEN month_series.m = 3 THEN l.m3
                            WHEN month_series.m = 4 THEN l.m4
                            WHEN month_series.m = 5 THEN l.m5
                            WHEN month_series.m = 6 THEN l.m6
                            WHEN month_series.m = 7 THEN l.m7
                            WHEN month_series.m = 8 THEN l.m8
                            WHEN month_series.m = 9 THEN l.m9
                            WHEN month_series.m = 10 THEN l.m10
                            WHEN month_series.m = 11 THEN l.m11
                            WHEN month_series.m = 12 THEN l.m12
                        END as plan_amount,
                        0 as actual_amount
                    FROM corporate_operating_financial l
                    JOIN corporate_operating_plan pl ON l.plan_id = pl.id
                    JOIN corporate_financial_item i ON l.item_id = i.id
                    CROSS JOIN generate_series(1,12) as month_series(m)
                    WHERE pl.state = 'approved' AND l.is_section = False AND l.is_total = False

                    UNION ALL

                    -- B. FINANCIAL ACTUALS
                    SELECT 
                        e.department_id,
                        e.company_id,
                        i.name as item_name,
                        e.category as financial_category,
                        e.fiscal_year,
                        e.period_month,
                        e.period_quarter,
                        0 as plan_amount,
                        e.actual_amount as actual_amount
                    FROM corporate_execution_financial e
                    JOIN corporate_financial_item i ON e.item_id = i.id
                ) as sub_f

                UNION ALL

                /* =============================================
                   3. CAPEX: PLAN vs ACTUAL
                   ============================================= */
                SELECT
                    row_number() OVER () + 2000000 as id,
                    'capex' as report_type,
                    sub_c.department_id,
                    sub_c.company_id,
                    sub_c.item_name,
                    NULL as financial_category,
                    sub_c.fiscal_year,
                    sub_c.period_month,
                    sub_c.period_quarter,
                    sub_c.plan_amount,
                    sub_c.actual_amount,
                    (sub_c.actual_amount - sub_c.plan_amount) as variance,
                    CASE WHEN sub_c.plan_amount > 0 THEN (sub_c.actual_amount / sub_c.plan_amount) * 100 ELSE 0 END as achievement_percent
                FROM (
                    -- A. CAPEX PLAN (Note: Capex is Quarterly in plan, mapping to last month of Q)
                    SELECT 
                        pl.department_id,
                        pl.company_id,
                        m.name as item_name,
                        pl.fiscal_year,
                        month_series.m as period_month,
                        CASE 
                            WHEN month_series.m BETWEEN 1 AND 3 THEN 'q1'
                            WHEN month_series.m BETWEEN 4 AND 6 THEN 'q2'
                            WHEN month_series.m BETWEEN 7 AND 9 THEN 'q3'
                            ELSE 'q4' 
                        END as period_quarter,
                        -- Mapping Quarterly Plan to the last month of that quarter for comparison
                        CASE 
                            WHEN month_series.m = 3 THEN l.q1_budget
                            WHEN month_series.m = 6 THEN l.q2_budget
                            WHEN month_series.m = 9 THEN l.q3_budget
                            WHEN month_series.m = 12 THEN l.q4_budget
                            ELSE 0
                        END as plan_amount,
                        0 as actual_amount
                    FROM corporate_operating_capex l
                    JOIN corporate_operating_plan pl ON l.plan_id = pl.id
                    JOIN corporate_capex_item m ON l.capex_item_id = m.id
                    CROSS JOIN generate_series(1,12) as month_series(m)
                    WHERE pl.state = 'approved'

                    UNION ALL

                    -- B. CAPEX ACTUALS
                    SELECT 
                        e.department_id,
                        e.company_id,
                        m.name as item_name,
                        e.fiscal_year,
                        e.period_month,
                        e.period_quarter,
                        0 as plan_amount,
                        e.actual_cost as actual_amount
                    FROM corporate_execution_capex e
                    JOIN corporate_capex_item m ON e.capex_item_id = m.id
                ) as sub_c

            )
        """ % (self._table,))