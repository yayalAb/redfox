from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FuelDeposit(models.Model):
    _name = 'fuel.deposit'
    _description = "Fuel Deposit"
    _order = 'date_start desc'

    name = fields.Char(string='Reference', required=True)
    is_active = fields.Boolean(
        string='Active',
        store=True,
        compute='_compute_is_active',
        inverse='_inverse_is_active'
    )
    manual_deactivate = fields.Boolean(default=False, invisible=True)

    date_start = fields.Date(string='Start Date', required=True, default=lambda self: fields.Date.today())
    date_end = fields.Date(string='End Date')
    initial_amount = fields.Monetary(string='Initial Amount')
    remaining_amount = fields.Monetary(string='Remaining Amount', compute='_compute_remaining_amount', store=True)
    used_amount = fields.Monetary(string='Used Amount', compute='_compute_used_amount', store=True)
    fuel_logs = fields.One2many('fleet.vehicle.log.fuel', 'fuel_deposit_id', string="Fuel Logs")
    fuel_logs_count = fields.Integer(string='Fuel Logs Count', compute='_compute_fuel_logs_count', store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # Compute fuel logs count
    @api.depends('fuel_logs')
    def _compute_fuel_logs_count(self):
        for record in self:
            record.fuel_logs_count = len(record.fuel_logs)

    # Compute is_active with manual override
    @api.depends('remaining_amount', 'used_amount', 'initial_amount', 'manual_deactivate')
    def _compute_is_active(self):
        for record in self:
            if record.manual_deactivate:
                record.is_active = False
            else:
                record.is_active = (
                    record.remaining_amount > 0 and
                    record.used_amount < record.initial_amount
                )

    def _inverse_is_active(self):
        """Allow user to manually deactivate/reactivate."""
        for record in self:
            record.manual_deactivate = not record.is_active

    # Compute remaining amount
    @api.depends('initial_amount', 'used_amount')
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = (record.initial_amount or 0) - (record.used_amount or 0)

    # Compute used amount from related fuel logs
    @api.depends('fuel_logs.amount')
    def _compute_used_amount(self):
        for record in self:
            record.used_amount = sum(log.amount for log in record.fuel_logs)

    # Only one is_active deposit at a time
    @api.constrains('is_active')
    def _check_single_is_active(self):
        for record in self:
            if record.is_active:
                other_is_active = self.search_count([
                    ('is_active', '=', True),
                    ('id', '!=', record.id)
                ])
                if other_is_active > 0:
                    raise ValidationError("Only one fuel deposit can be is_active at a time.")

    # Prevent used amount from exceeding initial
    @api.constrains('used_amount', 'remaining_amount')
    def _constraint_deposit_amount(self):
        for record in self:
            if record.used_amount > record.initial_amount:
                raise ValidationError("Used amount cannot be greater than initial amount.")
            if record.remaining_amount < 0:
                raise ValidationError("Remaining amount cannot be less than 0.")

    # Override write to set end date when deactivated
    def write(self, vals):
        if 'is_active' in vals and not vals['is_active']:
            for record in self:
                if record.is_active:  # was is_active before
                    vals = dict(vals)  # avoid mutating same dict
                    vals['date_end'] = fields.Date.today()
                    super(FuelDeposit, record).write(vals)
            return True
        return super().write(vals)

    # Button: deactivate deposit
    def action_deactivate(self):
        for record in self:
            if not record.is_active:
                raise ValidationError("This deposit is already inis_active.")
            record.write({'is_active': False})
    
    def action_activate(self):
        for record in self:
            if record.is_active:
                raise ValidationError("This deposit is already active.")
            record.write({'is_active': True})

    # Button: transfer funds to is_active deposit
    def action_transfer_to_active(self):
        self.ensure_one()
        if self.is_active:
            raise ValidationError("You cannot transfer funds from an is_active deposit.")
        if self.remaining_amount <= 0:
            raise ValidationError("No remaining amount to transfer.")

        is_active_deposit = self.search([('is_active', '=', True)], limit=1)
        if not is_active_deposit:
            raise ValidationError("No is_active deposit found to transfer funds to.")

        # Transfer all remaining funds
        transfer_amount = self.remaining_amount
        is_active_deposit.write({'initial_amount': is_active_deposit.initial_amount + transfer_amount})
        self.write({'initial_amount': self.initial_amount - transfer_amount})

    # Optional: auto-deactivate if empty (but respect manual flag)
    @api.onchange('remaining_amount')
    def _auto_deactivate_if_empty(self):
        for record in self:
            if record.remaining_amount <= 0 and not record.manual_deactivate:
                record.is_active = False
                record.manual_deactivate = True

    def action_view_fuel_logs(self):
        """Open the fuel logs related to this deposit."""
        self.ensure_one()
        return {
            'name': 'Fuel Logs',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.log.fuel',
            'view_mode': 'list,form',
            'domain': [('fuel_deposit_id', '=', self.id)],
            'context': {'default_fuel_deposit_id': self.id}
        }
