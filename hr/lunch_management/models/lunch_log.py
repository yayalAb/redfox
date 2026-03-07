from odoo import models, fields, api, _


class LunchLog(models.Model):
    _name = 'lunch.log'
    _description = 'Employee Lunch Log'

    @api.model
    def _default_employee_id(self):
        # Check the context passed from the menu action
        if self.env.context.get('is_self_service'):
            employee = self.env.user.employee_id
            return employee.id if employee else None
        return None

    name = fields.Char(string='Reference', default=lambda self: _(
        'New'), copy=False, required=True, readonly=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, default=_default_employee_id)

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id')

    is_self_service = fields.Boolean(
        string="Self Service Entry",
        default=lambda self: self.env.context.get('is_self_service', False),
        copy=False
    )

    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    meal_type = fields.Selection(
        [('breakfast', 'Breakfast'), ('lunch', 'Lunch')],
        string='Meal Service',
        required=True,
        default='lunch',
        tracking=True
    )
    state = fields.Selection(
        [('draft', 'Draft'), ('ordered', 'Ordered'),
         ('unbilled', 'Unbilled'), ('billed', 'Billed')],
        string='Status',
        default='draft',
        readonly=True,
        copy=False,
        tracking=True
    )

    line_ids = fields.One2many(
        'lunch.log.line', 'lunch_log_id', string='Food Items')
    total_price = fields.Monetary(
        string='Total Price', compute='_compute_total_price', store=True)

    is_current_user_employee = fields.Boolean(
        string="Is Logged-in User's Lunch",
        compute='_compute_is_current_user_employee'
    )

    def action_make_unbilled(self):
        for rec in self:
            rec.state = "unbilled"

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'lunch.log') or _('New')
        res = super(LunchLog, self).create(vals)
        return res

    def _compute_is_current_user_employee(self):
        """
        Check if the lunch log belongs to the employee of the current user.
        """
        current_user_employee = self.env.user.employee_id
        for log in self:
            if log.employee_id and current_user_employee:
                log.is_current_user_employee = (
                    log.employee_id == current_user_employee)
            else:
                log.is_current_user_employee = False

    @api.depends('line_ids.price_subtotal')
    def _compute_total_price(self):
        for rec in self:
            # Create a list of all subtotals and sum them up
            rec.total_price = sum(line.price_subtotal for line in rec.line_ids)

    def action_confirm_order(self):
        self.sudo().write({'state': 'ordered'})

    def action_confirm_lunch(self):
        for rec in self:
            rec.state = "unbilled"


class LunchLogLine(models.Model):
    _name = 'lunch.log.line'
    _description = 'Employee Lunch Log Line'

    lunch_log_id = fields.Many2one(
        'lunch.log', string='Lunch Log', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Food Item', required=True, domain=[('is_meal', '=', True)])
    quantity = fields.Integer(string='Quantity', default=1, required=True)
    price_unit = fields.Monetary(compute='_compute_lunch_price')
    currency_id = fields.Many2one(
        'res.currency', related='lunch_log_id.currency_id')
    price_subtotal = fields.Monetary(
        string='Subtotal', compute='_compute_price_subtotal', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.quantity * line.price_unit

    @api.depends('product_id')
    def _compute_lunch_price(self):
        for line in self:
            line.price_unit = line.product_id.lst_price
