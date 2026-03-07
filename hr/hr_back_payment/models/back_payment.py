from odoo import models, fields, api, _

class BackPayment(models.Model):
    _name = 'hr.back.payment'
    _description = 'Employee Back Payment Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_default_currency_id(self):
        return self.env.company.currency_id.id

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_from = fields.Date('Back Pay From Date', required=True, help="The first month of the back payment period.")
    date_to = fields.Date('Back Pay To Date', required=True, help="The last month of the back payment period.")
    
    calculation_struct_id = fields.Many2one(
        'hr.payroll.structure',
        string="Calculation Structure",
        required=True,
        domain="[('type_id.name', '=', 'Back Payment Calculation')]",
        help="Select the special structure that contains all salary rules needed to calculate the current values."
    )
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', default=_get_default_currency_id)

    # --- OLD SALARY DATA (User Input) ---
    old_basic_salary = fields.Monetary(string="Old Basic Salary")
    old_house_rent_allowance = fields.Monetary(string="Old House Rent Allowance")
    old_dearness_allowance = fields.Monetary(string="Old Dearness Allowance")
    old_travel_allowance = fields.Monetary(string="Old Travel Allowance")
    old_meal_allowance = fields.Monetary(string="Old Meal Allowance")
    old_medical_allowance = fields.Monetary(string="Old Medical Allowance")
    old_position_allowance = fields.Monetary(string="Old Position Allowance")
    old_transport_home_allowance = fields.Monetary(string="Old Transport (Home) Allowance")
    old_transport_work_allowance = fields.Monetary(string="Old Transport (Work) Allowance")
    old_fuel_allowance = fields.Monetary(string="Old Fuel Allowance")
    old_cash_indemnity_allowance = fields.Monetary(string="Old Cash Indemnity Allowance")
    old_professional_allowance = fields.Monetary(string="Old Professional Allowance")
    old_other_allowance = fields.Monetary(string="Old Other Allowance")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_payroll', 'In Payroll'),
        ('done', 'Done'),
    ], string='Status', default='draft', tracking=True, copy=False, index=True)

    payslip_batch_id = fields.Many2one('hr.payslip.run', string='Processed in Batch', readonly=True, copy=False)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.back.payment') or _('New')
        return super(BackPayment, self).create(vals)

    def action_set_to_draft(self):
        # This button should now work for both 'done' and 'in_payroll' states
        self.write({'state': 'draft'})
        # Also find any payslips linked to this and remove the link
        payslips = self.env['hr.payslip'].search([('back_payment_id', 'in', self.ids)])
        if payslips:
            payslips.write({'back_payment_id': False})