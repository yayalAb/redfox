# -*- coding: utf-8 -*-

import re
from odoo import models, fields, api


class PayslipRun(models.Model):
    _inherit = 'hr.salary.rule'
    is_basic = fields.Boolean(string='Is Base Rule')


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.model
    def get_salary_rule_variable_breakdown(self, batch1_id, batch2_id, employee_id, rule_id):
        """Return variable values used by some salary rule formulas for the given employee in both batches.

        This is meant to display formulas like:
          result = contract.wage * 0.11 * payslip.calculate_active_rate + payslip.old_contract_id.wage * 0.11 * payslip.old_active_rate

        We substitute variable values while preserving the formula structure.
        """
        # Get the rule to access its formula
        rule = self.env['hr.salary.rule'].browse(rule_id)
        formula = rule.amount_python_compute or ''

        def _get_payslip(run_id):
            return self.env["hr.payslip"].search(
                [
                    ("payslip_run_id", "=", int(run_id)),
                    ("employee_id", "=", int(employee_id)),
                    ("state", "!=", "cancel"),
                ],
                order="id desc",
                limit=1,
            )

        def _float_or_0(val):
            try:
                return float(val or 0.0)
            except Exception:
                return 0.0

        def _extract(payslip):
            if not payslip:
                return {
                    "payslip_id": None,
                    "contract_wage": 0.0,
                    "calculate_active_rate": 0.0,
                    "calculate_active_rate_worked_days": "0.00",
                    "calculate_active_rate_display": "0.00",
                    "old_contract_wage": 0.0,
                    "old_active_rate": 0.0,
                    "old_active_rate_worked_days": "0.00",
                    "old_active_rate_display": "0.00",
                    "line_amount": 0.0,
                    "line_quantity": 0.0,
                    "line_rate": 0.0,
                    "categories": {},
                    "contract_fields": {},
                    "old_contract_fields": {},
                    "employee_fields": {},
                }
            
            # Default values if fields don't exist in this database/customization
            contract_wage = _float_or_0(
                getattr(getattr(payslip, "contract_id", False), "wage", 0.0))
            active_rate = _float_or_0(
                getattr(payslip, "calculate_active_rate", 0.0))
            old_contract_wage = _float_or_0(
                getattr(getattr(payslip, "old_contract_id", False), "wage", 0.0))
            old_active_rate = _float_or_0(
                getattr(payslip, "old_active_rate", 0.0))
            
            # Extract all contract fields that might be used in formulas
            contract_fields = {}
            employee_fields = {}  # Extract employee fields accessed via contract.employee_id
            if hasattr(payslip, "contract_id") and payslip.contract_id:
                contract = payslip.contract_id
                # Get all monetary and float fields from contract
                for field_name, field in contract._fields.items():
                    if field.type in ('monetary', 'float') and not field.relational:
                        try:
                            value = getattr(contract, field_name, None)
                            if value is not None:
                                contract_fields[field_name] = _float_or_0(value)
                        except Exception:
                            pass
                
                # Extract employee fields that might be accessed via contract.employee_id
                if contract.employee_id:
                    employee = contract.employee_id
                    # Get boolean and other fields from employee
                    for field_name, field in employee._fields.items():
                        if field.type in ('boolean', 'float', 'monetary', 'integer') and not field.relational:
                            try:
                                value = getattr(employee, field_name, None)
                                if value is not None:
                                    if field.type == 'boolean':
                                        employee_fields[field_name] = bool(value)
                                    else:
                                        employee_fields[field_name] = _float_or_0(value)
                            except Exception:
                                pass
            
            # Extract old contract fields
            old_contract_fields = {}
            if hasattr(payslip, "old_contract_id") and payslip.old_contract_id:
                old_contract = payslip.old_contract_id
                for field_name, field in old_contract._fields.items():
                    if field.type in ('monetary', 'float') and not field.relational:
                        try:
                            value = getattr(old_contract, field_name, None)
                            if value is not None:
                                old_contract_fields[field_name] = _float_or_0(value)
                            else:
                                # Set to 0.0 if field exists but is None
                                old_contract_fields[field_name] = 0.0
                        except Exception:
                            # If field doesn't exist, set to 0.0
                            old_contract_fields[field_name] = 0.0
            else:
                # If no old contract, still extract fields from current contract structure
                # to ensure we can substitute them (they'll be 0.0)
                if hasattr(payslip, "contract_id") and payslip.contract_id:
                    contract = payslip.contract_id
                    for field_name, field in contract._fields.items():
                        if field.type in ('monetary', 'float') and not field.relational:
                            if field_name not in old_contract_fields:
                                old_contract_fields[field_name] = 0.0

            # Calculate actual worked days based on how calculate_active_rate works
            # calculate_active_rate = active_days / total_days
            # Display format: (date_from to date_end / total_days)
            calculate_active_rate_worked_days = "0.00"  # Default value
            calculate_active_rate_display = "0.00"  # Default display format
            total_days = 0
            if hasattr(payslip, "date_from") and hasattr(payslip, "date_to"):
                if payslip.date_from and payslip.date_to:
                    total_days = (payslip.date_to - payslip.date_from).days + 1
                    date_from_str = payslip.date_from.strftime('%Y-%m-%d')
                    date_to_str = payslip.date_to.strftime('%Y-%m-%d')
                    
                    # Calculate active days (overlap between contract and payslip period)
                    if hasattr(payslip, "contract_id") and payslip.contract_id:
                        contract_start = payslip.contract_id.date_start
                        contract_end = payslip.contract_id.date_end or payslip.date_to
                        period_start = payslip.date_from
                        period_end = payslip.date_to
                        
                        overlap_start = max(contract_start, period_start)
                        overlap_end = min(contract_end, period_end)
                        
                        if overlap_start <= overlap_end:
                            active_days = (overlap_end - overlap_start).days + 1
                            calculate_active_rate_worked_days = f"{active_days:.2f}"
                            # Format: (worked_days / total_days)
                            calculate_active_rate_display = f"({active_days:.0f} / {total_days})"
                        else:
                            calculate_active_rate_worked_days = "0.00"
                            calculate_active_rate_display = f"(0 / {total_days})"
                    else:
                        # Fallback: use rate * total_days
                        worked_days = total_days * active_rate
                        calculate_active_rate_worked_days = f"{worked_days:.2f}"
                        calculate_active_rate_display = f"({worked_days:.0f} / {total_days})"

            # Calculate actual worked days for old contract
            old_active_rate_worked_days = "0.00"  # Default to 0.00
            old_active_rate_display = "0.00"  # Default display format
            if hasattr(payslip, "old_contract_id") and payslip.old_contract_id:
                if hasattr(payslip, "date_from") and hasattr(payslip, "date_to"):
                    if payslip.date_from and payslip.date_to:
                        total_days_old = (payslip.date_to - payslip.date_from).days + 1
                        date_from_str = payslip.date_from.strftime('%Y-%m-%d')
                        date_to_str = payslip.date_to.strftime('%Y-%m-%d')
                        
                        # Calculate active days for old contract
                        old_contract_start = payslip.old_contract_id.date_start
                        old_contract_end = payslip.old_contract_id.date_end or payslip.date_to
                        period_start = payslip.date_from
                        period_end = payslip.date_to
                        
                        overlap_start = max(old_contract_start, period_start)
                        overlap_end = min(old_contract_end, period_end)
                        
                        if overlap_start <= overlap_end:
                            active_days_old = (overlap_end - overlap_start).days + 1
                            old_active_rate_worked_days = f"{active_days_old:.2f}"
                            # Format: (worked_days / total_days)
                            old_active_rate_display = f"({active_days_old:.0f} / {total_days_old})"
                        else:
                            old_active_rate_worked_days = "0.00"
                            old_active_rate_display = f"(0 / {total_days_old})"
            else:
                # Set default display format even when no old contract
                if hasattr(payslip, "date_from") and hasattr(payslip, "date_to") and payslip.date_from and payslip.date_to:
                    total_days_old = (payslip.date_to - payslip.date_from).days + 1
                    old_active_rate_display = f"(0 / {total_days_old})"
            
            # Ensure calculate_active_rate_worked_days has a default value
            if not calculate_active_rate_worked_days:
                calculate_active_rate_worked_days = "0.00"
            if not calculate_active_rate_display:
                calculate_active_rate_display = "0.00"
            if not old_active_rate_display:
                old_active_rate_display = "0.00"

            # Also include the payslip line computational components (amount/qty/rate) as a fallback.
            line = self.env["hr.payslip.line"].search(
                [("slip_id", "=", payslip.id),
                 ("salary_rule_id", "=", int(rule_id))],
                limit=1,
            )
            amount = _float_or_0(getattr(line, "amount", 0.0))
            quantity = _float_or_0(getattr(line, "quantity", 0.0))
            rate = _float_or_0(getattr(line, "rate", 0.0))
            
            # Extract category totals from payslip lines
            categories = {}
            if payslip and hasattr(payslip, "line_ids"):
                for payslip_line in payslip.line_ids:
                    if payslip_line.category_id and payslip_line.category_id.code:
                        category_code = payslip_line.category_id.code
                        if category_code not in categories:
                            categories[category_code] = 0.0
                        categories[category_code] += payslip_line.total or 0.0

            return {
                "payslip_id": payslip.id,
                "contract_wage": contract_wage,
                "calculate_active_rate": active_rate,
                "calculate_active_rate_worked_days": calculate_active_rate_worked_days,
                "calculate_active_rate_display": calculate_active_rate_display,
                "old_contract_wage": old_contract_wage,
                "old_active_rate": old_active_rate,
                "old_active_rate_worked_days": old_active_rate_worked_days,
                "old_active_rate_display": old_active_rate_display,
                "line_amount": amount,
                "line_quantity": quantity,
                "line_rate": rate,
                "categories": categories,  # Add category totals
                "contract_fields": contract_fields,  # Add all contract fields
                "old_contract_fields": old_contract_fields,  # Add all old contract fields
                "employee_fields": employee_fields,  # Add employee fields
                "employee_name": payslip.contract_id.employee_id.name if (hasattr(payslip, "contract_id") and payslip.contract_id and payslip.contract_id.employee_id) else "",
                "contract_employee_id": payslip.contract_id.employee_id.id if (hasattr(payslip, "contract_id") and payslip.contract_id and payslip.contract_id.employee_id) else None,
            }

        def _substitute_formula(formula_str, values_dict):
            """Substitute variable values in formula while preserving structure."""
            if not formula_str:
                return ""
            
            # Work with the entire formula
            result = formula_str
            
            # First pass: Substitute all known values (categories, contract fields, etc.)
            # This will help us evaluate intermediate variables
            
            # Substitute categories first
            categories = values_dict.get('categories', {})
            if categories:
                category_pattern = r"categories\s*\[\s*['\"]([A-Z0-9_]+)['\"]\s*\]"
                matches = re.findall(category_pattern, result)
                for category_code in matches:
                    category_value = categories.get(category_code, 0.0)
                    pattern = r"categories\s*\[\s*['\"]" + re.escape(category_code) + r"['\"]\s*\]"
                    result = re.sub(pattern, f"{category_value:.2f}", result)
            
            # Substitute contract fields - sort by length to avoid partial matches
            contract_fields = values_dict.get('contract_fields', {})
            sorted_contract_fields = sorted(contract_fields.items(), key=lambda x: len(x[0]), reverse=True)
            for field_name, field_value in sorted_contract_fields:
                replacement = f"{field_value:.2f}"
                # Handle both underscore and dot notation
                pattern1 = r'\bcontract\.' + re.escape(field_name) + r'\b'
                result = re.sub(pattern1, replacement, result)
                field_name_dots = field_name.replace('_', '.')
                pattern2 = r'\bcontract\.' + re.escape(field_name_dots) + r'\b'
                result = re.sub(pattern2, replacement, result)
            
            # Substitute employee fields accessed via contract.employee_id.field_name
            employee_fields = values_dict.get('employee_fields', {})
            for field_name, field_value in employee_fields.items():
                # Handle contract.employee_id.pays_pension pattern
                pattern1 = r'\bcontract\.employee_id\.' + re.escape(field_name) + r'\b'
                if isinstance(field_value, bool):
                    replacement = 'True' if field_value else 'False'
                else:
                    replacement = f"{field_value:.2f}"
                result = re.sub(pattern1, replacement, result)
                # Also handle with dots
                field_name_dots = field_name.replace('_', '.')
                pattern2 = r'\bcontract\.employee_id\.' + re.escape(field_name_dots) + r'\b'
                result = re.sub(pattern2, replacement, result)
            
            # Substitute other known variables
            contract_wage = values_dict.get('contract_wage', 0.0)
            pattern = r'\bcontract\.wage\b'
            result = re.sub(pattern, f"{contract_wage:.2f}", result)
            
            calculate_active_rate_display = values_dict.get('calculate_active_rate_display', '0.00')
            pattern = r'\bpayslip\.calculate_active_rate\b'
            result = re.sub(pattern, calculate_active_rate_display, result)
            
            old_contract_wage = values_dict.get('old_contract_wage', 0.0)
            pattern = r'\b(?:payslip\.)?old_contract_id\.wage\b'
            result = re.sub(pattern, f"{old_contract_wage:.2f}", result)
            
            # Substitute old contract fields - do this before other substitutions to avoid conflicts
            old_contract_fields = values_dict.get('old_contract_fields', {})
            # Sort by field name length (longest first) to avoid partial matches
            sorted_fields = sorted(old_contract_fields.items(), key=lambda x: len(x[0]), reverse=True)
            for field_name, field_value in sorted_fields:
                replacement = f"{field_value:.2f}"
                # Handle both underscore and dot notation, with and without payslip prefix
                # Pattern 1: payslip.old_contract_id.field_name or old_contract_id.field_name (with underscore)
                pattern1 = r'\b(?:payslip\.)?old_contract_id\.' + re.escape(field_name) + r'\b'
                result = re.sub(pattern1, replacement, result)
                # Pattern 2: payslip.old_contract_id.field.name (with dots)
                field_name_dots = field_name.replace('_', '.')
                pattern2 = r'\b(?:payslip\.)?old_contract_id\.' + re.escape(field_name_dots) + r'\b'
                result = re.sub(pattern2, replacement, result)
            
            old_active_rate_display = values_dict.get('old_active_rate_display', '0.00')
            pattern = r'\bpayslip\.old_active_rate\b'
            result = re.sub(pattern, old_active_rate_display, result)
            
            # Second pass: Evaluate intermediate variables (e.g., a = 5000.00)
            # Extract variable assignments and calculate their values
            lines = result.split('\n')
            variable_values = {}
            
            for line in lines:
                stripped = line.strip()
                # Look for simple variable assignments (var = value)
                if '=' in stripped and not any(stripped.startswith(x) for x in ['if', 'elif', 'else', 'result', '#']):
                    parts = stripped.split('=', 1)
                    if len(parts) == 2:
                        var_name = parts[0].strip()
                        var_expr = parts[1].strip().rstrip(';')
                        
                        # Handle string assignments (e.g., employee_specific_name = "Teklit Gebregergs")
                        if var_expr.startswith('"') and var_expr.endswith('"'):
                            variable_values[var_name] = var_expr.strip('"')
                        elif var_expr.startswith("'") and var_expr.endswith("'"):
                            variable_values[var_name] = var_expr.strip("'")
                        # Check if expression is now just numbers/operators (after substitution)
                        elif re.match(r'^[\d\.\+\-\*\/\(\)\s\-]+$', var_expr):
                            try:
                                # Safe calculation
                                calculated_value = float(eval(var_expr))
                                variable_values[var_name] = calculated_value
                            except:
                                pass
                        # Handle variable references (e.g., a = categories['GROSS'] after substitution)
                        elif var_expr in variable_values:
                            variable_values[var_name] = variable_values[var_expr]
                        # Handle dictionary access that was already substituted (e.g., a = 50000.00)
                        elif re.match(r'^[\d\.]+$', var_expr):
                            try:
                                variable_values[var_name] = float(var_expr)
                            except:
                                pass
            
            # Third pass: Substitute intermediate variables in the formula
            for var_name, var_value in variable_values.items():
                # Only substitute standalone variable names (not part of other names)
                pattern = r'\b' + re.escape(var_name) + r'\b'
                # Handle string vs numeric values
                if isinstance(var_value, str):
                    result = re.sub(pattern, f'"{var_value}"', result)
                else:
                    result = re.sub(pattern, f"{var_value:.2f}", result)
            
            # Fourth pass: Evaluate conditions and extract the correct result branch
            # This is complex - we need to evaluate nested if/elif/else and find the executed branch
            result_lines = result.split('\n')
            condition_stack = []  # Stack to track nested conditions
            executed_result = None
            last_condition_was_true = False  # Track if we found a true condition branch
            
            # Build evaluation context from variable_values
            eval_context = {}
            for var_name, var_value in variable_values.items():
                eval_context[var_name] = var_value
            
            # Also add categories and other values to eval_context
            categories = values_dict.get('categories', {})
            for cat_code, cat_value in categories.items():
                eval_context[f"categories['{cat_code}']"] = cat_value
            
            # Add employee name for string comparisons
            employee_name = values_dict.get('employee_name', '')
            # Create a mock object for contract.employee_id.name comparisons
            class MockEmployee:
                def __init__(self, name):
                    self.name = name
            class MockContract:
                def __init__(self, employee_name):
                    self.employee_id = MockEmployee(employee_name)
            eval_context['contract'] = MockContract(employee_name)
            eval_context['contract.employee_id.name'] = employee_name
            
            i = 0
            while i < len(result_lines):
                line = result_lines[i]
                stripped = line.strip()
                indent_level = len(line) - len(line.lstrip())
                
                # Check for if/elif/else conditions
                if stripped.startswith('if ') or stripped.startswith('elif ') or stripped.startswith('else:'):
                    # Manage condition stack based on indentation
                    # Remove conditions at same or deeper indentation (new block level)
                    condition_stack = [c for c in condition_stack if c['indent'] < indent_level]
                    
                    if stripped.startswith('else:'):
                        # else executes only if no previous if/elif in this block was true
                        # Check if any condition at this indent level was true
                        parent_conditions = [c for c in condition_stack if c['indent'] == indent_level - 4]
                        condition_result = not any(c['result'] for c in parent_conditions) if parent_conditions else True
                        condition_text = 'else'
                    else:
                        condition_text = stripped.split(':', 1)[0].replace('if ', '').replace('elif ', '').strip()
                        # Try to evaluate the condition
                        try:
                            # The condition_text should already have variables substituted from previous passes
                            # But we need to handle string comparisons and other complex expressions
                            condition_eval = condition_text
                            
                            # Handle contract.employee_id checks - substitute with boolean
                            if 'contract.employee_id' in condition_eval and 'contract.employee_id.name' not in condition_eval:
                                # Simple existence check - if employee_name exists, it's True
                                condition_eval = condition_eval.replace('contract.employee_id', 'True' if employee_name else 'False')
                            
                            # Try to parse and evaluate
                            condition_result = bool(eval(condition_eval, eval_context))
                        except Exception as e:
                            # If evaluation fails, try simpler approach
                            try:
                                # Check if it's a simple boolean or comparison
                                if 'True' in condition_text:
                                    condition_result = True
                                elif 'False' in condition_text:
                                    condition_result = False
                                elif '!=' in condition_text or '==' in condition_text:
                                    # String comparison - try to evaluate parts
                                    if '!=' in condition_text:
                                        parts = condition_text.split('!=')
                                        if len(parts) == 2:
                                            left = parts[0].strip()
                                            right = parts[1].strip().strip('"').strip("'")
                                            # If right is a string literal, compare
                                            if left in eval_context:
                                                condition_result = str(eval_context[left]) != right
                                            else:
                                                condition_result = True  # Assume true if can't evaluate
                                    else:
                                        condition_result = True  # Default to true if can't evaluate
                                else:
                                    # Try numeric comparison
                                    condition_result = bool(eval(condition_eval, eval_context))
                            except:
                                # Last resort: if contains True or positive number, assume true
                                condition_result = 'True' in condition_text or ('0' not in condition_text and 'False' not in condition_text)
                    
                    condition_stack.append({
                        'indent': indent_level,
                        'result': condition_result,
                        'line': i,
                        'text': condition_text
                    })
                    
                    # Track if this condition branch is true
                    if condition_result:
                        last_condition_was_true = True
                
                # Check for result assignments
                if 'result' in stripped and '=' in stripped:
                    # Extract the result value
                    if '=' in stripped:
                        parts = stripped.split('=', 1)
                        if len(parts) == 2:
                            value_part = parts[1].strip()
                            # Remove any Python syntax
                            value_part = re.sub(r'\s*(#|\\).*$', '', value_part).strip()
                            if value_part:
                                # Check if this result should execute based on condition stack
                                # Result executes if all conditions in stack are true
                                should_execute = all(c['result'] for c in condition_stack) if condition_stack else True
                                
                                if should_execute:
                                    # Try to evaluate the result expression
                                    try:
                                        # Check if it's a numeric expression
                                        eval_result = float(eval(value_part, eval_context))
                                        # Prefer non-zero results, but keep the last one if all are zero
                                        if eval_result != 0:
                                            executed_result = value_part
                                            last_condition_was_true = True  # Found a non-zero result
                                        elif executed_result is None:
                                            executed_result = value_part
                                    except:
                                        # If evaluation fails, use as-is
                                        if executed_result is None:
                                            executed_result = value_part
                                        elif '0' not in value_part:
                                            executed_result = value_part
                
                i += 1
            
            # Use the executed result if found
            if executed_result:
                result = executed_result
            else:
                # Fallback: find the last non-zero result assignment
                for line in reversed(result_lines):
                    if 'result' in line and '=' in line:
                        stripped = line.strip()
                        if '=' in stripped:
                            parts = stripped.split('=', 1)
                            if len(parts) == 2:
                                result_val = parts[1].strip()
                                result_val = re.sub(r'\s*(#|\\).*$', '', result_val).strip()
                                # Try to evaluate
                                try:
                                    eval_val = float(eval(result_val, eval_context))
                                    if eval_val != 0:
                                        result = result_val
                                        break
                                except:
                                    if '0' not in result_val:
                                        result = result_val
                                        break
            
            return result.strip()

        ps1 = _get_payslip(batch1_id)
        ps2 = _get_payslip(batch2_id)
        
        batch1_data = _extract(ps1) if ps1 else None
        batch2_data = _extract(ps2) if ps2 else None
        
        # Add substituted formula for each batch
        if batch1_data:
            batch1_data['formula_with_values'] = _substitute_formula(formula, batch1_data)
        if batch2_data:
            batch2_data['formula_with_values'] = _substitute_formula(formula, batch2_data)

        return {
            "batch1": batch1_data,
            "batch2": batch2_data,
        }

    @api.model
    def get_payroll_difference_data(self, batch1_id=None, batch2_id=None):
        """
        Get payroll difference data between two batches.

        :param batch1_id: ID of first batch (default: most recent)
        :param batch2_id: ID of second batch (default: second most recent)
        :return: Dictionary containing employees, salary rules, and amounts
        """
        # Get batches - default to two most recent
        if not batch1_id or not batch2_id:
            batches = self.search([], order='date_end desc, id desc', limit=2)
            if len(batches) < 2:
                return {
                    'employees': [],
                    'salary_rules': [],
                    'data': {},
                    'batch1': {},
                    'batch2': {},
                    'error': 'Need at least 2 payroll batches to compare'
                }
            batch1 = batches[0] if not batch1_id else self.browse(batch1_id)
            batch2 = batches[1] if not batch2_id else self.browse(batch2_id)
        else:
            batch1 = self.browse(batch1_id)
            batch2 = self.browse(batch2_id)

        # Get all payslips from both batches
        payslips1 = batch1.slip_ids.filtered(lambda p: p.state != 'cancel')
        payslips2 = batch2.slip_ids.filtered(lambda p: p.state != 'cancel')

        # Get all unique employees from both batches
        employee_ids = (payslips1.mapped('employee_id') |
                        payslips2.mapped('employee_id')).ids
        employees = self.env['hr.employee'].browse(employee_ids)

        # Get all unique salary rules that appear on payslips - only base rules
        # Deduplicate by code within the company context to prevent showing the same rule twice
        # Since batches are company-specific, rules should also be company-specific
        rule_codes_seen = {}  # Track by code: {code: rule_id} to keep first occurrence
        
        # Get company from batches (both batches should be from same company)
        company_id = batch1.company_id.id if batch1.company_id else (batch2.company_id.id if batch2.company_id else False)
        
        for payslip in payslips1 | payslips2:
            for line in payslip.line_ids:
                if line.appears_on_payslip and line.salary_rule_id:
                    # Check if rule is a base rule (is_basic = True)
                    rule = line.salary_rule_id
                    is_basic = getattr(rule, 'is_basic', False)
                    if is_basic:
                        rule_code = rule.code or ''
                        # Only add if we haven't seen this code before
                        # Also ensure rule belongs to the same company (if company filtering is needed)
                        if rule_code and rule_code not in rule_codes_seen:
                            # Check if rule's structure belongs to the same company
                            rule_company_id = rule.struct_id.company_id.id if rule.struct_id and rule.struct_id.company_id else False
                            if not company_id or not rule_company_id or rule_company_id == company_id:
                                rule_codes_seen[rule_code] = rule.id
        
        # Get unique rules by their IDs
        rule_ids = list(rule_codes_seen.values())
        salary_rules = self.env['hr.salary.rule'].browse(rule_ids).sorted('sequence')

        # Build data structure: {employee_id: {rule_code: {batch1: amount, batch2: amount, batch1_details: {}, batch2_details: {}}}}
        # Use rule_code as key to aggregate amounts for same code with different IDs
        data = {}
        
        # Create mapping from rule_code to selected rule_id
        code_to_rule_id = {code: rule_id for code, rule_id in rule_codes_seen.items()}

        # Process batch1 - aggregate amounts by code
        for payslip in payslips1:
            emp_id = payslip.employee_id.id
            if emp_id not in data:
                data[emp_id] = {}

            for line in payslip.line_ids:
                if line.appears_on_payslip and line.salary_rule_id:
                    rule = line.salary_rule_id
                    is_basic = getattr(rule, 'is_basic', False)
                    if is_basic:
                        rule_code = rule.code or ''
                        # Use the selected rule_id for this code
                        rule_id = code_to_rule_id.get(rule_code)
                        if rule_id and rule_code:
                            if rule_code not in data[emp_id]:
                                data[emp_id][rule_code] = {
                                    'rule_id': rule_id,
                                    'batch1': 0.0,
                                    'batch2': 0.0,
                                    'batch1_details': {'amount': 0.0, 'quantity': 0.0, 'rate': 0.0},
                                    'batch2_details': {'amount': 0.0, 'quantity': 0.0, 'rate': 0.0}
                                }
                            # Sum amounts if multiple payslips exist for same employee or same code with different IDs
                            data[emp_id][rule_code]['batch1'] += line.total or 0.0
                            # Store details (for first payslip, or average if multiple)
                            if data[emp_id][rule_code]['batch1'] == line.total:
                                data[emp_id][rule_code]['batch1_details'] = {
                                    'amount': line.amount or 0.0,
                                    'quantity': line.quantity or 0.0,
                                    'rate': line.rate or 0.0
                                }

        # Process batch2 - aggregate amounts by code
        for payslip in payslips2:
            emp_id = payslip.employee_id.id
            if emp_id not in data:
                data[emp_id] = {}

            for line in payslip.line_ids:
                if line.appears_on_payslip and line.salary_rule_id:
                    rule = line.salary_rule_id
                    is_basic = getattr(rule, 'is_basic', False)
                    if is_basic:
                        rule_code = rule.code or ''
                        # Use the selected rule_id for this code
                        rule_id = code_to_rule_id.get(rule_code)
                        if rule_id and rule_code:
                            if rule_code not in data[emp_id]:
                                data[emp_id][rule_code] = {
                                    'rule_id': rule_id,
                                    'batch1': 0.0,
                                    'batch2': 0.0,
                                    'batch1_details': {'amount': 0.0, 'quantity': 0.0, 'rate': 0.0},
                                    'batch2_details': {'amount': 0.0, 'quantity': 0.0, 'rate': 0.0}
                                }
                            # Sum amounts if multiple payslips exist for same employee or same code with different IDs
                            data[emp_id][rule_code]['batch2'] += line.total or 0.0
                            # Store details (for first payslip, or average if multiple)
                            if data[emp_id][rule_code]['batch2'] == line.total:
                                data[emp_id][rule_code]['batch2_details'] = {
                                    'amount': line.amount or 0.0,
                                    'quantity': line.quantity or 0.0,
                                    'rate': line.rate or 0.0
                                }

        # Format employees data
        employees_data = []
        for emp in employees.sorted('name'):
            # Try to get employee identification (badge_id, identification_id, or registration_number)
            emp_id_number = ''
            if hasattr(emp, 'badge_id') and emp.badge_id:
                emp_id_number = emp.badge_id
            elif hasattr(emp, 'identification_id') and emp.identification_id:
                emp_id_number = emp.identification_id
            elif hasattr(emp, 'registration_number') and emp.registration_number:
                emp_id_number = emp.registration_number

            employees_data.append({
                'id': emp.id,
                'name': emp.name,
                'employee_id': emp_id_number,
            })

        # Format salary rules data - only include base rules (is_basic = True)
        # Deduplicate by code to prevent showing the same rule twice
        rules_data = []
        seen_codes = set()
        for rule in salary_rules:
            # Check if rule has is_basic field and if it's True
            is_basic = getattr(rule, 'is_basic', False)
            if is_basic:
                rule_code = rule.code or ''
                # Only add if we haven't seen this code before
                if rule_code not in seen_codes:
                    rule_data = {
                        'id': rule.id,
                        'name': rule.name,
                        'code': rule_code,
                        'sequence': rule.sequence,
                        'formula': rule.amount_python_compute or rule.amount_fix or '',
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix or 0.0,
                        'amount_percentage': rule.amount_percentage or 0.0,
                        'is_basic': is_basic,
                    }
                    rules_data.append(rule_data)
                    seen_codes.add(rule_code)

        return {
            'employees': employees_data,
            'salary_rules': rules_data,
            'data': data,
            'batch1': {
                'id': batch1.id,
                'name': batch1.name,
                'date_start': batch1.date_start.isoformat() if batch1.date_start else '',
                'date_end': batch1.date_end.isoformat() if batch1.date_end else '',
            },
            'batch2': {
                'id': batch2.id,
                'name': batch2.name,
                'date_start': batch2.date_start.isoformat() if batch2.date_start else '',
                'date_end': batch2.date_end.isoformat() if batch2.date_end else '',
            },
        }

    @api.model
    def get_available_batches(self):
        """Get list of available payroll batches for selection"""
        # Filter batches by current company so the dropdown is company-based
        company = self.env.company
        domain = [('company_id', '=', company.id)]
        batches = self.search(domain, order='date_end desc, id desc')
        result = []
        for batch in batches:
            # Get state label
            state_label = dict(self._fields['state'].selection).get(
                batch.state, batch.state)
            result.append({
                'id': batch.id,
                'name': batch.name,
                'date_start': batch.date_start.isoformat() if batch.date_start else '',
                'date_end': batch.date_end.isoformat() if batch.date_end else '',
                'state': batch.state,
                'state_label': state_label,
            })
        return result
