# -*- coding: utf-8 -*-
from odoo import models, fields, api

# 1. ACTIVITY FEEDER
class ProjectLogActivityFeeder(models.Model):
    _inherit = 'project.task.log.activity'

    @api.model_create_multi
    def create(self, vals_list):
        print("DEBUG: Data Feeder Create Triggered")
        records = super(ProjectLogActivityFeeder, self).create(vals_list)
        for rec in records: 
            rec._sync_to_execution_table()
        return records

    def write(self, vals):
        res = super(ProjectLogActivityFeeder, self).write(vals)
        for rec in self: 
            rec._sync_to_execution_table()
        return res

    def _sync_to_execution_table(self):
        print(f"DEBUG: Syncing Log {self.id}")
        try:
            # 1. Check if Task exists
            if not self.task_id or not self.task_id.exists():
                return

            # 2. Check if AOP Line exists
            aop_line = self.task_id.aop_activity_id
            if not aop_line or not aop_line.exists():
                print("ERROR: No AOP Activity Linked to this Task") 
                return

            # 3. Check if Plan and Master Data exist (The cause of your error)
            if not aop_line.plan_id or not aop_line.plan_id.exists():
                print("ERROR: No Plan Linked to this AOP Activity")
                return
            if not aop_line.activity_master_id or not aop_line.activity_master_id.exists():
                print("ERROR: No Activity Master Linked to this AOP Activity")
                return

            print(f"DEBUG: All checks passed, updating execution table for {self.task_id.aop_activity_id.activity_master_id.name}")
            
            # 4. Update Execution Table (Use sudo to bypass permission issues)
            self.env['corporate.execution.activity'].sudo()._update_actuals(
                aop_line.plan_id.company_id,
                aop_line.plan_id.department_id,
                aop_line.activity_master_id,
                self.date,
                self.quantity
            )
        except Exception as e:
            # Log error but do not crash the server/upgrade
            print(f"WARNING: Data Feeder skipped a record due to error: {str(e)}")


# 2. FINANCIAL FEEDER
class ProjectLogFinancialFeeder(models.Model):
    _inherit = 'project.task.log.financial'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProjectLogFinancialFeeder, self).create(vals_list)
        for rec in records: rec._sync_to_execution_table()
        return records

    def write(self, vals):
        res = super(ProjectLogFinancialFeeder, self).write(vals)
        for rec in self: rec._sync_to_execution_table()
        return res

    def _sync_to_execution_table(self):
        try:
            if not self.task_id or not self.task_id.exists(): return
            aop_line = self.task_id.aop_financial_id
            if not aop_line or not aop_line.exists(): return
            if not aop_line.item_id or not aop_line.item_id.exists(): return

            self.env['corporate.execution.financial'].sudo()._update_actuals(
                aop_line.plan_id.company_id,
                aop_line.plan_id.department_id,
                aop_line.item_id,
                self.date,
                self.amount
            )
        except Exception:
            pass


# 3. CAPEX FEEDER
class ProjectLogCapexFeeder(models.Model):
    _inherit = 'project.task.log.capex'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProjectLogCapexFeeder, self).create(vals_list)
        for rec in records: rec._sync_to_execution_table()
        return records
    
    def write(self, vals):
        res = super(ProjectLogCapexFeeder, self).write(vals)
        for rec in self: rec._sync_to_execution_table()
        return res

    def _sync_to_execution_table(self):
        try:
            if not self.task_id or not self.task_id.exists(): return
            aop_line = self.task_id.aop_capex_id
            if not aop_line or not aop_line.exists(): return
            if not aop_line.capex_item_id or not aop_line.capex_item_id.exists(): return

            self.env['corporate.execution.capex'].sudo()._update_actuals(
                aop_line.plan_id.company_id,
                aop_line.plan_id.department_id,
                aop_line.capex_item_id,
                self.date,
                self.qty,
                self.cost
            )
        except Exception:
            pass