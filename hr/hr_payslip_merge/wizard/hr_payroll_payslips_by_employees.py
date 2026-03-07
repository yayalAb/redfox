# -*- coding: utf-8 -*-
from odoo import models, api, _
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    # Removed compute_sheet override - auto-adding happens in hr.contract model instead

    def _filter_contracts(self, contracts):
        """
        Override to filter contracts so only the most recent contract per employee is used.
        This prevents duplicate payslips when an employee has multiple contracts in the same period.
        Most recent is determined by the contract start date (date_start).
        """
        # Group contracts by employee
        contracts_by_employee = defaultdict(list)
        for contract in contracts:
            contracts_by_employee[contract.employee_id.id].append(contract)
        
        # For each employee, select only the most recent contract based on start date
        filtered_contracts = self.env['hr.contract']
        for employee_id, employee_contracts in contracts_by_employee.items():
            if len(employee_contracts) > 1:
                # Filter contracts with date_start and sort by date_start (most recent = latest date_start)
                contracts_with_date = [c for c in employee_contracts if c.date_start]
                contracts_without_date = [c for c in employee_contracts if not c.date_start]
                
                if contracts_with_date:
                    # Select contract with the latest (most recent) start date
                    most_recent = max(contracts_with_date, key=lambda c: c.date_start)
                    filtered_contracts |= most_recent
                    _logger.info("HR Payslip Merge: Employee %s has %d contracts, using most recent by start date: %s (start: %s)", 
                               employee_contracts[0].employee_id.name, 
                               len(employee_contracts),
                               most_recent.name if most_recent.name else f"Contract {most_recent.id}",
                               most_recent.date_start)
                elif contracts_without_date:
                    # If no contracts have date_start, use the most recently created one
                    most_recent = max(contracts_without_date, key=lambda c: c.create_date)
                    filtered_contracts |= most_recent
                    _logger.warning("HR Payslip Merge: Employee %s has %d contracts without start date, using most recently created: %s", 
                                  employee_contracts[0].employee_id.name,
                                  len(employee_contracts),
                                  most_recent.name if most_recent.name else f"Contract {most_recent.id}")
            else:
                filtered_contracts |= employee_contracts[0]
        
        return filtered_contracts
