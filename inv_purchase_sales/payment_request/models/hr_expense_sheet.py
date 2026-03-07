from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    reference = fields.Char(
        string='Reference', index=True, default='New')
    can_user_approve = fields.Boolean(
        string="Can Current User Approve",
        compute='_compute_can_user_authorize'
    )
    state = fields.Selection(
        selection=[
            ('draft', 'To Submit'),
            ('submit', 'Submitted'),
            ('verify', 'To Verify'),
            ('authorize', 'Authorized'),
            ('approve', 'Approved'),
            ('processed', 'Processed'),
            ('post', 'Posted'),
            ('done', 'Done'),
            ('cancel', 'Refused')
        ],
        string="Status",
        compute='_compute_state', store=True, readonly=True,
        index=True,
        required=True,
        default='draft',
        tracking=True,
        copy=False,
    )
    approval_state = fields.Selection(
        selection=[
            ('submit', 'Submitted'),
            ('verify', 'Verified'),
            ('authorize', 'Authorized'),
            ('approve', 'Approved'),
            ('processed', 'Processed'),
            ('cancel', 'Refused'),
        ],
        copy=False,
    )
    verified_by = fields.Many2one('res.users', string='Verified By')
    authorized_by = fields.Many2one('res.users', string='Authorized By')
    approved_by = fields.Many2one(
        'res.users', string='Approved by', copy=False,
        help="The user who approved the expense report."
    )
    processed_by = fields.Many2one(
        'res.users', string='Processed by', copy=False,
        help="The user who processed the expense report."
    )
    purpose = fields.Text(string="Request Purpose")
    remark = fields.Text(string="Remark")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code('employee.expense') or 'New'
        return super(HrExpenseSheet, self).create(vals_list)

    def _compute_can_user_authorize(self):
        """
        Compute if the current user has the right to authorize this specific request.
        """
        is_low_approver = self.env.user.has_group(
            'payment_request.group_purchase_approver_low')
        is_high_approver = self.env.user.has_group(
            'payment_request.group_purchase_approver_high')

        for order in self:
            low_condition = is_low_approver and order.total_amount <= 500000
            high_condition = is_high_approver and order.total_amount > 500000
            if low_condition or high_condition:
                order.can_user_approve = True
            else:
                order.can_user_approve = False

    def action_verify_expense_sheets(self):
        """ Sends the expense report from 'submit' to 'verify' state. """
        self.filtered(lambda s: s.state == 'submit')._do_verify()

    def _do_verify(self):
        """ Internal method to set the report to 'verify'. """
        for sheet in self:
            sheet.write({'approval_state': 'verify',
                        'verified_by': self.env.user})
        self.activity_update()

    def action_authorize_expense_sheets(self):
        self.filtered(lambda s: s.state == 'verify')._do_authorize()

    def _do_authorize(self):
        for sheet in self:
            sheet.write({'approval_state': 'authorize',
                        'authorized_by': self.env.user})
        self.activity_update()

    def _do_approve(self):
        sheets_to_approve = self.filtered(lambda s: s.state in {'authorize'})
        sheets_to_approve._check_can_create_move()
        sheets_to_approve._do_create_moves()
        for sheet in sheets_to_approve:
            sheet.write({
                'approval_state': 'approve',
                'user_id': sheet.user_id or self.env.user,
                'approved_by': self.env.user,
                'approval_date': fields.Date.context_today(sheet),
            })
        self.activity_update()

    def action_process_expense_sheets(self):
        """Processes the expense report from 'approve' to 'processed' state."""
        self.filtered(lambda s: s.state == 'approve')._do_process()

    def _do_process(self):
        """Internal method to set the report to 'processed'."""
        for sheet in self:
            sheet.write({
                'approval_state': 'processed',
                'processed_by': self.env.user,
            })
        self.activity_update()

    @api.depends('account_move_ids', 'payment_state', 'approval_state')
    def _compute_state(self):
        super()._compute_state()

        for sheet in self:
            if sheet.approval_state == 'verify' and not sheet.account_move_ids:
                sheet.state = 'verify'
            elif sheet.approval_state == 'processed':
                sheet.state = 'processed'

    def write(self, values):
        res = super().write(values)

        edit_lines = 'expense_line_ids' in values
        edit_states = 'state' in values or 'approval_state' in values

        if edit_states or edit_lines:
            for sheet in self.filtered(lambda sheet: not sheet.expense_line_ids):
                # ADDED 'verify' to the states check
                if sheet.state in {'submit', 'verify', 'approve', 'post', 'done'}:
                    if edit_lines and not sheet.expense_line_ids:
                        raise UserError(
                            _("You cannot remove all expenses from a submitted, approved or paid expense report."))
                    else:
                        raise UserError(
                            _("This expense report is empty. You cannot submit or approve an empty expense report."))
        return res

    def activity_update(self):
        # Run original logic
        super().activity_update()
        reports_requiring_feedback = self.env['hr.expense.sheet']
        reports_activity_unlink = self.env['hr.expense.sheet']
        for expense_report in self:
            # Keep activity open for both 'submit' and 'verify' until approved/refused
            if expense_report.state in ('submit', 'verify'):
                expense_report.activity_schedule(
                    'hr_expense.mail_act_expense_approval',
                    user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif expense_report.state == 'approve':
                reports_requiring_feedback |= expense_report
            elif expense_report.state in {'draft', 'cancel'}:
                reports_activity_unlink |= expense_report

        if reports_requiring_feedback:
            reports_requiring_feedback.activity_feedback(
                ['hr_expense.mail_act_expense_approval'])
        if reports_activity_unlink:
            reports_activity_unlink.activity_unlink(
                ['hr_expense.mail_act_expense_approval'])

    def _check_can_create_move(self):
        """
        Override to allow move creation when the state is 'verify' 
        (the state just before approval in the new flow).
        """
        if any(not sheet.expense_line_ids for sheet in self):
            raise UserError(
                _("You cannot create accounting entries for an expense report without expenses."))

        # ORIGINAL: if any(sheet.state != 'submit' for sheet in self):
        if any(sheet.state not in ('submit', 'verify', 'authorize') for sheet in self):
            raise UserError(
                _("You can only generate an accounting entry for verified/approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(
                _("Please specify an expense journal in order to generate accounting entries."))

        if False in self.mapped('payment_mode'):
            raise UserError(_(
                "Please specify if the expenses for this report were paid by the company, or the employee"
            ))
