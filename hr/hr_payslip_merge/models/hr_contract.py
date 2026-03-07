# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to automatically add employee to existing payslip batches
        if the new contract overlaps with any batch period.
        """
        contracts = super(HrContract, self).create(vals_list)
        
        # After contract creation, check if employee should be added to existing batches
        for contract in contracts:
            if contract.employee_id and contract.state in ('open', 'close') and contract.active:
                contract._add_to_overlapping_batches()
        
        return contracts

    def write(self, vals):
        """
        Override write to add employee to batches when contract becomes active/running
        """
        res = super(HrContract, self).write(vals)
        
        # If contract state changed to open/close or became active, check for batches
        if any(key in vals for key in ['state', 'active', 'date_start', 'date_end']):
            for contract in self:
                if contract.employee_id and contract.state in ('open', 'close') and contract.active:
                    contract._add_to_overlapping_batches()
        
        return res

    def _add_to_overlapping_batches(self):
        """
        Add employee to existing payslip batches if contract overlaps with batch period.
        """
        self.ensure_one()
        
        if not self.employee_id or not self.date_start:
            return
        
        # Find all payslip batches (runs) that overlap with this contract
        # Contract overlaps with batch if:
        # - Contract starts before or on batch end AND contract ends after or on batch start
        # - Or contract has no end date and starts before or on batch end
        contract_end = self.date_end or fields.Date.today()
        
        overlapping_batches = self.env['hr.payslip.run'].search([
            ('state', 'in', ['draft', 'verify']),  # Only add to batches that aren't closed/paid
            ('company_id', '=', self.company_id.id),
        ])
        
        # Filter batches that actually overlap with contract period
        overlapping_batches = overlapping_batches.filtered(lambda b: 
            self.date_start <= b.date_end and contract_end >= b.date_start
        )
        
        for batch in overlapping_batches:
            # Check if employee already has a payslip in this batch
            existing_payslip = self.env['hr.payslip'].search([
                ('payslip_run_id', '=', batch.id),
                ('employee_id', '=', self.employee_id.id),
            ], limit=1)
            
            if existing_payslip:
                _logger.info("HR Payslip Merge: Employee %s already has payslip in batch %s, skipping", 
                           self.employee_id.name, batch.name)
                continue
            
            # Check if employee has contracts that overlap with batch period
            employee_contracts = self.employee_id._get_contracts(
                batch.date_start,
                batch.date_end,
                states=['open', 'close']
            ).filtered(lambda c: c.active)
            
            if not employee_contracts:
                continue
            
            # Use the most recent contract (by start date)
            contracts_with_date = employee_contracts.filtered(lambda c: c.date_start)
            if contracts_with_date:
                contract_to_use = max(contracts_with_date, key=lambda c: c.date_start)
            else:
                contract_to_use = max(employee_contracts, key=lambda c: c.create_date)
            
            # Create payslip for this employee in the batch
            try:
                Payslip = self.env['hr.payslip']
                default_values = Payslip.default_get(Payslip.fields_get())
                
                payslip_vals = {
                    'name': _('New Payslip'),
                    'employee_id': self.employee_id.id,
                    'payslip_run_id': batch.id,
                    'date_from': batch.date_start,
                    'date_to': batch.date_end,
                    'contract_id': contract_to_use.id,
                    'struct_id': contract_to_use.structure_type_id.default_struct_id.id if contract_to_use.structure_type_id else False,
                }
                payslip_vals.update(default_values)
                
                payslip = Payslip.with_context(tracking_disable=True).create(payslip_vals)
                payslip._compute_name()
                payslip.compute_sheet()
                payslip.write({'state': 'draft'})  # Keep as draft initially
                
                _logger.info("HR Payslip Merge: Auto-created payslip for employee %s in batch %s using contract %s", 
                           self.employee_id.name, batch.name, contract_to_use.name or f"Contract {contract_to_use.id}")
            except Exception as e:
                _logger.error("HR Payslip Merge: Failed to auto-create payslip for employee %s in batch %s: %s", 
                            self.employee_id.name, batch.name, str(e))

