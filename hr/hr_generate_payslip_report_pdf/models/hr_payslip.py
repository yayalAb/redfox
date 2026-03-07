# -*- coding: utf-8 -*-

import logging
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_generate_payslip_report(self):
        """
        This method is called when the 'Generate Payslip Report' button is clicked.
        It now calls the PDF report action.
        """
        _logger.info("Triggering PDF report for %d payslips.", len(self))

        # It's good practice to check if any records were selected.
        if not self:
            return

        # You might want to filter out payslips that are not in a printable state.
        printable_payslips = self.filtered(
            lambda p: p.state not in ['draft', 'cancel'])
        if not printable_payslips:
            raise UserError(
                _("You can only generate reports for payslips that are confirmed. Please remove any draft or cancelled payslips from your selection."))

        # --- NEW LOGIC: Calculate min and max dates ---
        # The mapped() function creates a list of all date_from values, then min() finds the earliest.
        # min_date_from = min(printable_payslips.mapped('date_from'))
        # # Similarly, max() finds the latest date_to.
        # max_date_to = max(printable_payslips.mapped('date_to'))
        # min_date_from_str = min_date_from.strftime('%B %d, %Y')
        # max_date_to_str = max_date_to.strftime('%B %d, %Y')
        # This is the core change: Call the report action
        # The name must match the XML ID you created: 'module_name.action_id'

        periods = set()
        for payslip in printable_payslips:
            if payslip.date_from and payslip.date_to:
                period = payslip.date_from.strftime('%B %Y')
                periods.add(period)
        periods = sorted(periods)  # Sort for consistent display

        # Join periods into a readable string
        periods_str = ", ".join(periods) if periods else "N/A"
        periods_str = "August 2025"

        # return self.env.ref('hr_generate_payslip_report_pdf.action_report_payslip_summary').with_context(landscape=True, min_date_from=min_date_from_str, max_date_to=max_date_to_str).report_action(printable_payslips)
        return self.env.ref('hr_generate_payslip_report_pdf.action_report_payslip_summary').with_context(landscape=True, periods_str=periods_str).report_action(printable_payslips)
