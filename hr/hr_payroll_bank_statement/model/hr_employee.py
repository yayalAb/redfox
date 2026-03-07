# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    bank_account_ids = fields.Many2many(
        'res.partner.bank',
        compute='_compute_bank_account_ids',
        inverse='_inverse_bank_account_ids',
        store=True,
        string="Bank Accounts",
        help="All bank accounts associated with this employee's work contact."
    )

    @api.depends('work_contact_id.bank_ids')
    def _compute_bank_account_ids(self):
        """Compute bank accounts from work contact."""
        for employee in self:
            if employee.work_contact_id:
                employee.bank_account_ids = employee.work_contact_id.bank_ids
            else:
                employee.bank_account_ids = False

    def _inverse_bank_account_ids(self):
        """Update work contact's bank accounts when bank_account_ids is modified."""
        for employee in self:
            if employee.work_contact_id:
                # Update the work contact's bank_ids to match bank_account_ids
                employee.work_contact_id.bank_ids = employee.bank_account_ids

