from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class PurchaseGuarante(models.Model):
    _name = "purchase.guarante"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Guarantee Name",
                       compute="_compute_name", store=True)
    company_id = fields.Many2one(
        'res.company', string="Company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', string="Purchase Order", required=True)
    customs_guaranteed_amount = fields.Monetary(
        string="Customs Guaranteed Amount", required=True)
    guaranteed_amount_before_interest = fields.Monetary(
        string="Guaranteed Amount (75%)", compute="_compute_guaranteed_amount", store=True, readonly=True)
    paid_amount = fields.Monetary(
        string="Paid Amount (25%)", compute="_compute_guaranteed_amount", store=True, readonly=True)
    interest_amount = fields.Monetary(
        string="Interest Amount", compute="_compute_interest_amount", store=True, readonly=True)
    guaranteed_amount_after_interest = fields.Monetary(
        string="Guaranteed Amount After Interest", compute="_compute_interest_amount", store=True, readonly=True)
    lc_number = fields.Char(string="LC Number")
    foreign_currency_id = fields.Many2one(
        'res.currency', string="Foreign Currency", default=lambda self: self.env.company.currency_id)
    foreign_currency_amount = fields.Monetary(
        string="Foreign Currency Amount", currency_field='foreign_currency_id')
    declaration_number = fields.Char(
        string="Declaration Number", required=True)
    guaranteed_bank = fields.Char(string="Guaranteed Bank", required=True,)
    guarantee_period = fields.Integer(
        string="Guarantee Period (months)", required=True)
    reference = fields.Char(string="Reference", required=True)
    start_date = fields.Date(string="Start Date", required=True,)
    expiry_date = fields.Date(string="Expiry Date",
                              compute="_compute_expiry_date", store=True)
    customs_branch_id = fields.Many2one(
        'customs.branch', string="Customs Branch")
    account_type = fields.Selection(
        related='customs_branch_id.account_type', string="Account Type")
    account_number = fields.Char(string="Account Number")
    state = fields.Selection([
        ('in_progress', 'In Progress'),
        ('paid', 'Paid'),
        ('extended', 'Extended'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], default='in_progress', string="Remark")
    payment_request_ids = fields.One2many(
        'hr.expense.sheet', 'guarantee_id', string="Payment Requests")
    payment_count = fields.Integer(
        string="Payment Request Count", compute="_compute_payment_count")
    payment_line_ids = fields.One2many(
        'purchase.guarante.payment.line',
        'guarantee_id',
        compute="_compute_payment_lines",
        string="Payment Schedule",
        store=True
    )

    @api.depends('payment_request_ids')
    def _compute_payment_count(self):
        for record in self:
            record.payment_count = len(record.payment_request_ids)

    @api.onchange('customs_branch_id')
    def _onchange_customs_branch_id(self):
        if self.customs_branch_id:
            self.account_number = self.customs_branch_id.account_number

    @api.constrains('customs_guaranteed_amount')
    def _check_customs_guaranteed_amount(self):
        for record in self:
            if record.customs_guaranteed_amount <= 0:
                raise ValidationError(
                    "Customs guaranteed amount must be positive.")

    @api.depends('guaranteed_amount_before_interest', 'guarantee_period', 'start_date', 'customs_branch_id')
    def _compute_payment_lines(self):
        for guarantee in self:
            guarantee.payment_line_ids = [(5, 0, 0)]
            if guarantee.guarantee_period > 0 and guarantee.start_date and guarantee.guaranteed_amount_before_interest > 0 and guarantee.customs_branch_id.monthly_payment:
                monthly_amount = guarantee.guaranteed_amount_before_interest / \
                    guarantee.guarantee_period

                lines_to_create = []
                for month_num in range(1, guarantee.guarantee_period + 1):
                    due_date = guarantee.start_date + \
                        relativedelta(months=month_num)
                    interest = monthly_amount * 0.215 * month_num * 30 / 365
                    lines_to_create.append((0, 0, {
                        'sequence': month_num,
                        'payment_date': due_date,
                        'amount_before_interest': monthly_amount,
                        'interest': interest
                    }))

                guarantee.payment_line_ids = lines_to_create

    @api.depends('start_date', 'guarantee_period')
    def _compute_expiry_date(self):
        for record in self:
            if record.start_date and record.guarantee_period:
                record.expiry_date = record.start_date + \
                    relativedelta(months=record.guarantee_period)
            else:
                record.expiry_date = False

    @api.depends('purchase_order_id')
    def _compute_name(self):
        for record in self:
            record.name = f"Guarantee for {record.purchase_order_id.name}"

    @api.constrains('guarantee_period')
    def _check_guarantee_period(self):
        for record in self:
            if record.guarantee_period <= 0 or record.guarantee_period > 12:
                raise ValidationError(
                    "Guarantee period must be positive and less than or equal to 12.")

    @api.depends('customs_guaranteed_amount')
    def _compute_guaranteed_amount(self):
        for record in self:
            record.guaranteed_amount_before_interest = record.customs_guaranteed_amount * 0.75
            record.paid_amount = record.customs_guaranteed_amount * 0.25

    @api.depends('guaranteed_amount_before_interest', 'guarantee_period')
    def _compute_interest_amount(self):
        for record in self:
            month = record.guarantee_period
            record.interest_amount = record.guaranteed_amount_before_interest * \
                0.215 * month * 30 / 365
            record.guaranteed_amount_after_interest = record.guaranteed_amount_before_interest + \
                record.interest_amount

    def action_view_purchase_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_id.id,
            'target': 'current',
        }

    def action_pay(self):
        self.ensure_one()
        self.write({'state': 'paid'})

    def action_extend(self):
        self.ensure_one()
        self.write({'state': 'extended'})

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})

    def action_create_payment_request(self):
        self.ensure_one()
        product = self.env['product.product'].search(
            [('can_be_expensed', '=', True)], limit=1)

        if not product:
            raise UserError(
                _("No product found that can be expensed. Please configure a service product with 'Can be Expensed' checked."))

        expense_line_vals = {
            'name': f"25% Guarantee Payment: {self.declaration_number}",
            'product_id': product.id,
            'employee_id': self.env.user.employee_ids and self.env.user.employee_ids[0].id or False,
            'quantity': 1,
            'total_amount_currency': self.paid_amount,
            'price_unit': self.paid_amount,
            'currency_id': self.currency_id.id or self.env.company.currency_id.id,
            'payment_mode': 'company_account',
            'date': fields.Date.today(),
        }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Request',
            'res_model': 'hr.expense.sheet',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_name': f"Payment Request: {self.name}",
                'default_employee_id': self.env.user.employee_ids and self.env.user.employee_ids[0].id or False,
                'default_payment_mode': 'company_account',
                'default_guarantee_id': self.id,
                'default_foreign_purchase': True,
                'default_purchase_order_id': self.purchase_order_id.id,
                'default_declaration_number': self.declaration_number,
                'default_lc_number': self.lc_number,
                'default_account_type': self.account_type,
                'default_account_number': self.account_number,
                'default_foreign_currency_amount': self.foreign_currency_amount,
                'default_expense_line_ids': [(0, 0, expense_line_vals)],
            }
        }

    def action_view_payment_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Requests',
            'res_model': 'hr.expense.sheet',
            'view_mode': 'list,form',
            'domain': [('guarantee_id', '=', self.id)],
            'context': {'default_guarantee_id': self.id},
            'target': 'current',
        }

    def _cron_guarantee_reminders(self):

        _logger.info(
            "Starting cron job for final guarantee expiry reminders...")
        today = date.today()

        records_to_expire = self.search([
            ('expiry_date', '<', today),
            ('state', 'in', ['in_progress', 'extended']),
            # <-- Only for non-monthly
            ('customs_branch_id.monthly_payment', '=', False)
        ])
        if records_to_expire:
            records_to_expire.write({'state': 'expired'})

        reminders = [30, 14, 1]

        activity_type = self.env.ref(
            "purchase_guarante.mail_act_purchase_guarantee_to_renew", raise_if_not_found=False)
        if not activity_type:
            _logger.warning(
                "Activity type 'Guarantee to Renew' not found. Skipping final expiry cron.")
            return

        notification_group = self.env.ref(
            'purchase_guarante.purchase_guarantee_group_expiry', raise_if_not_found=False)
        if not notification_group or not notification_group.users:
            _logger.warning(
                "Group 'purchase_guarantee_group_expiry' has no users. Skipping final expiry cron.")
            return

        users_to_notify = notification_group.users

        for days in reminders:
            target_date = today + relativedelta(days=days)
            # Find guarantees for branches without monthly payments that are expiring
            expiring_guarantees = self.search([
                ('state', 'in', ['in_progress', 'extended']),
                ('expiry_date', '=', target_date),
                # <-- ADDED THIS CRITICAL CONDITION
                ('customs_branch_id.monthly_payment', '=', False)
            ])

            _logger.info(
                f"Found {len(expiring_guarantees)} non-monthly guarantees expiring in {days} days.")
            for guarantee in expiring_guarantees:
                for user in users_to_notify:
                    already_exists = self.env["mail.activity"].search_count([
                        ("res_id", "=", guarantee.id),
                        ("res_model", "=", "purchase.guarante"),
                        ("activity_type_id", "=", activity_type.id),
                        ("user_id", "=", user.id),
                        ("summary", "=", f"Guarantee expires in {days} days"),
                    ])
                    if not already_exists:
                        self.env["mail.activity"].create({
                            "res_id": guarantee.id,
                            "res_model_id": self.env.ref("purchase_guarante.model_purchase_guarante").id,
                            "activity_type_id": activity_type.id,
                            "user_id": user.id,
                            "summary": _(f"Guarantee expires in {days} days"),
                            "note": _(f"The guarantee {guarantee.name} will expire in {days} days (on {guarantee.expiry_date})."),
                            "date_deadline": today,
                        })

    def _cron_payment_deadline_reminders(self):

        _logger.info("Starting cron job for monthly payment line reminders...")
        today = date.today()
        PaymentLine = self.env['purchase.guarante.payment.line']

        try:
            activity_type = self.env.ref(
                "purchase_guarante.mail_act_payment_deadline_reminder")
            notification_group = self.env.ref(
                'purchase_guarante.purchase_guarantee_group_payment_reminders')
        except ValueError:
            _logger.warning(
                "Required data (activity type or user group) for payment reminders not found. Skipping.")
            return

        if not notification_group or not notification_group.users:
            _logger.warning(
                "Group 'purchase_guarantee_group_payment_reminders' has no users. Skipping reminder cron.")
            return

        users_to_notify = notification_group.users

        # Rule: Notify 7 days before each monthly payment for branches with monthly_payment=True
        target_date = today + relativedelta(days=7)
        monthly_lines = PaymentLine.search([
            ('state', '=', 'to_pay'),
            ('payment_date', '=', target_date),
            ('guarantee_id.customs_branch_id.monthly_payment',
             '=', True),  # <-- MODIFIED CONDITION
        ])

        _logger.info(
            f"Found {len(monthly_lines)} payment lines for monthly payment branches due on {target_date}.")
        for line in monthly_lines:
            summary = _(f"Payment due in 7 days for {line.guarantee_id.name}")
            note = _(
                f"Monthly payment of {line.total_amount} {line.currency_id.symbol} for guarantee {line.guarantee_id.name} is due on {line.payment_date}.")
            line._create_reminder_activity(
                activity_type, users_to_notify, summary, note)


class PurchaseGuarantePaymentLine(models.Model):
    _name = "purchase.guarante.payment.line"
    _description = "Purchase Guarantee Payment Line"
    _order = "payment_date asc"

    guarantee_id = fields.Many2one(
        'purchase.guarante', string="Guarantee", required=True, ondelete='cascade')
    company_id = fields.Many2one(related='guarantee_id.company_id', store=True)
    currency_id = fields.Many2one(
        related='guarantee_id.currency_id', store=True)

    name = fields.Char(string="Description", compute="_compute_name")
    sequence = fields.Integer(string="Month Number", default=1)
    payment_date = fields.Date(string="Payment Due Date")
    amount_before_interest = fields.Monetary(string="Payment Amount")
    interest = fields.Monetary(string="Interest Amount")
    total_amount = fields.Monetary(
        string="Total Amount", compute="_compute_total_amount")
    state = fields.Selection([
        ('to_pay', 'To Pay'),
        ('paid', 'Paid'),
    ], default='to_pay', string="Status")

    @api.depends('amount_before_interest', 'interest')
    def _compute_total_amount(self):
        for line in self:
            line.total_amount = line.amount_before_interest + line.interest

    @api.depends('guarantee_id.name', 'sequence')
    def _compute_name(self):
        for line in self:
            if line.guarantee_id:
                line.name = f"{line.guarantee_id.name} - Month {line.sequence}"
            else:
                line.name = f"Month {line.sequence}"

    def action_mark_as_paid(self):
        self.write({'state': 'paid'})

    def _create_reminder_activity(self, activity_type, users, summary, note):

        self.ensure_one()
        model_id = self.env.ref(
            'purchase_guarante.model_purchase_guarante_payment_line').id
        for user in users:
            if not self.env["mail.activity"].search_count([
                ("res_id", "=", self.id),
                ("res_model_id", "=", model_id),
                ("activity_type_id", "=", activity_type.id),
                ("user_id", "=", user.id),
            ]):
                self.env["mail.activity"].create({
                    "res_id": self.id,
                    "res_model_id": model_id,
                    "activity_type_id": activity_type.id,
                    "user_id": user.id,
                    "summary": summary,
                    "note": note,
                    "date_deadline": date.today(),
                })
                _logger.info(
                    f"Created payment reminder for user {user.name} on payment line {self.name}.")


class CustomsBranch(models.Model):
    _name = "customs.branch"
    _description = "Customs Branch"

    name = fields.Char(string="Branch Name", required=True)
    location = fields.Char(string="Location")
    monthly_payment = fields.Boolean(string="Monthly Payment", default=False)
    guarantee_ids = fields.One2many(
        'purchase.guarante', 'customs_branch_id', string="Guarantees")
    account_type = fields.Selection([
        ('direct', 'Direct Account'),
        ('deposit', 'Deposit Account'),
    ], string="Account Type", default='direct')
    account_number = fields.Char(string="Account Number")
