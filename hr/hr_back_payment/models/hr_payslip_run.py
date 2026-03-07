# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import logging

# Standard Odoo practice for enabling logging in this file
_logger = logging.getLogger(__name__)

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_generate_back_payments(self):
        """
        This is the main action triggered by the 'Generate Back-Payments' button.
        
        Workflow:
        1. Finds all back payment records in the 'Draft' state.
        2. For each record, it validates the employee's contract and batch details.
        3. It performs a direct, field-by-field comparison of old values (from the back payment record)
           and current values (from the employee's contract).
        4. If any positive differences are found, it creates a new payslip for the employee
           with the differences added to the 'Other Inputs' section.
        5. It updates the back payment record's state to 'In Payroll'.
        6. It includes detailed logging to the Odoo server log for easy debugging.
        """
        self.ensure_one()
        back_payment_records = self.env['hr.back.payment'].search([('state', '=', 'draft')])
        if not back_payment_records:
            raise UserError(_("There are no 'Draft' back payment records to process."))

        # This dictionary is the single source of truth for the calculation. It maps:
        # 'old_field_name' (on hr.back.payment) -> 
        #   'contract_field' (the corresponding current value field on hr.contract) ->
        #   'input_code' (the code of the hr.payslip.input.type to send the result to).
        # This uses the exact field names from your existing custom module.
        field_mapping = {
            'old_basic_salary':             {'contract_field': 'wage', 'input_code': 'BACKPAY_BASIC'},
            'old_house_rent_allowance':     {'contract_field': 'house_rent_allowance', 'input_code': 'BACKPAY_HRA'},
            'old_dearness_allowance':       {'contract_field': 'dearness_allowance', 'input_code': 'BACKPAY_DA'},
            'old_travel_allowance':         {'contract_field': 'travel_allowance', 'input_code': 'BACKPAY_TA'},
            'old_meal_allowance':           {'contract_field': 'meal_allowance', 'input_code': 'BACKPAY_MEAL'},
            'old_medical_allowance':        {'contract_field': 'medical_allowance', 'input_code': 'BACKPAY_MED'},
            'old_position_allowance':       {'contract_field': 'position_allowance', 'input_code': 'BACKPAY_POS'},
            'old_transport_home_allowance': {'contract_field': 'transport_home_allowance', 'input_code': 'BACKPAY_TRH'},
            'old_transport_work_allowance': {'contract_field': 'transport_work_allowance', 'input_code': 'BACKPAY_TRW'},
            'old_fuel_allowance':           {'contract_field': 'fuel_allowance', 'input_code': 'BACKPAY_FUEL'},
            'old_cash_indemnity_allowance': {'contract_field': 'cash_indemnity_allowance', 'input_code': 'BACKPAY_CASH'},
            'old_professional_allowance':   {'contract_field': 'professional_allowance', 'input_code': 'BACKPAY_PROF'},
            'old_other_allowance':          {'contract_field': 'other_allowance', 'input_code': 'BACKPAY_OTHER'},
        }

        # Pre-fetch all necessary input types from the database for efficiency
        all_input_codes = [v['input_code'] for v in field_mapping.values()]
        all_input_types = self.env['hr.payslip.input.type'].search([('code', 'in', all_input_codes)])
        input_type_map = {it.code: it.id for it in all_input_types}
        
        payslips_to_create = []
        records_to_process = self.env['hr.back.payment']

        for bp in back_payment_records:
            employee = bp.employee_id

            # --- START OF LOGGING BLOCK for this record ---
            _logger.info(f"--- Starting Detailed Calculation Check for {employee.name} (ID: {employee.id}) ---")
            
            # --- Validation 1: Check for a running contract ---
            contract = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
            if not contract:
                _logger.warning("Calculation stopped: No running contract found for this employee.")
                raise UserError(_("Skipping back payment for '%s' because they do not have a running contract.") % employee.name)
            
            _logger.info(f"Found running contract (ID: {contract.id}) with base wage: {contract.wage}")

            # --- Validation 2: Check for date overlap (silently skips if no overlap) ---
            if not (bp.date_from <= self.date_end and bp.date_to >= self.date_start):
                _logger.info("Skipping: Back payment period does not overlap with this batch's period.")
                continue

            # --- Validation 3: Prevent duplicate payslips in the same batch (silently skips) ---
            existing_payslip = self.env['hr.payslip'].search([('payslip_run_id', '=', self.id), ('employee_id', '=', employee.id)], limit=1)
            if existing_payslip:
                _logger.info("Skipping: Employee already has a payslip in this batch.")
                continue

            # --- Validation 4: Ensure the contract is configured to generate a payslip ---
            if not contract.structure_type_id.default_struct_id:
                _logger.warning(f"Calculation stopped: Contract's Salary Structure Type '{contract.structure_type_id.name}' has no Default Salary Structure set.")
                raise UserError(_("Cannot generate payslip for '%s' because their contract's Salary Structure Type ('%s') does not have a 'Default Salary Structure' set.") % (employee.name, contract.structure_type_id.name))

            # --- Main Calculation Logic ---
            months_count = relativedelta(min(bp.date_to, self.date_end), max(bp.date_from, self.date_start)).months + 1
            if months_count <= 0:
                continue

            input_lines = []
            _logger.info("--- Comparing Old Values vs. Current Contract Values ---")
            for old_field_name, mapping in field_mapping.items():
                # 1. Get Old Value from the back payment record
                old_value = getattr(bp, old_field_name, 0.0)

                # 2. Get Current Value directly from the employee's contract
                current_field_name = mapping['contract_field']
                current_value = getattr(contract, current_field_name, 0.0)

                # 3. Calculate the difference
                monthly_diff = current_value - old_value

                # 4. Log the result of the comparison for debugging
                _logger.info(f"CHECKING: {current_field_name} | Current Value on Contract = {current_value} | Old Value from Record = {old_value} | Difference = {monthly_diff}")

                # 5. If the difference is positive, prepare it as a payslip input
                if monthly_diff > 0:
                    total_diff = monthly_diff * months_count
                    input_code = mapping['input_code']
                    input_type_id = input_type_map.get(input_code)
                    if input_type_id:
                        input_lines.append((0, 0, {'input_type_id': input_type_id, 'amount': total_diff}))

            _logger.info(f"--- Finished Calculation Check. Found {len(input_lines)} positive difference(s). ---")

            # --- Validation 5: Check if any positive difference was found after the loop ---
            if not input_lines:
                raise UserError(_("Skipping back payment for '%s' because no positive difference was found. Please CHECK THE ODOO LOG FILE for a detailed calculation breakdown to see why.") % employee.name)

            # --- If all checks pass, prepare the data for the new payslip ---
            payslip_vals = {
                'name': f"Payslip for {employee.name} (with Back Pay) - {self.name}",
                'employee_id': employee.id,
                'date_from': self.date_start,
                'date_to': self.date_end,
                'payslip_run_id': self.id,
                'contract_id': contract.id,
                'struct_id': contract.structure_type_id.default_struct_id.id,
                'input_line_ids': input_lines,
                'back_payment_id': bp.id,
            }
            payslips_to_create.append(payslip_vals)
            records_to_process |= bp

        # --- Final Actions outside the loop ---
        if payslips_to_create:
            self.env['hr.payslip'].create(payslips_to_create)
            _logger.info(f"Successfully created {len(payslips_to_create)} new payslip(s) with back payments.")

        # Update the state of processed records to 'In Payroll'
        records_to_process.write({'state': 'in_payroll', 'payslip_batch_id': self.id})
        
        # Return an action to reload the view, which forces the smart button to update
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'main',
        }