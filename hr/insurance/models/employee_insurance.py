from odoo import models, fields, api, _
from datetime import timedelta
from datetime import date
from odoo.exceptions import ValidationError


class EmployeeInsurance(models.Model):
    _name = 'employee.insurance'

    name = fields.Many2one('employee.insurance.coverage', string="Reference")
    employee_id = fields.Many2one(
        'hr.employee', string="Employee", related='name.employee_id')
    start_date = fields.Date(string="Start date", related="name.from_date")
    end_date = fields.Date(string="End date", related="name.date_to")
    # company_id = fields.Many2one('res.company', related="employee_id.company_id")
    value = fields.Float(string="Value", related="name.total_claim")
    policy_type = fields.Many2one(
        'insurance.type', string="Policy type", related="name.category_id")
    provider_id = fields.Many2one(
        'insurance.provider', string="Insurance Provider", related="name.provider_id")
    total_annual_premium = fields.Float(
        string="Total Annual Premium", related='name.total_annual_premium')
    remark = fields.Text(string="Note",)
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'), (
        'approve', 'Approved'), ('reject', 'Reject'), ('expire', 'Expired')], default='draft')
    attachment = fields.Binary(string="Document")
    utilization_line_ids = fields.One2many(
        'employee.insurance.line', 'insurance_id', store=True, copy=True)
    # coverage_lines = fields.Many2many('employee.insurance.coverage', string='Coverage Lines', related="name.employee_id")
    total_utilization_amount = fields.Float(
        string='Total Utilization', compute='_compute_total_utilization')
    # employee_coverage_ids = fields.Many2many('employee.insurance.coverage', string="Coverages", related='employee_id.employee_id')
    remaining = fields.Float(
        string="Remaining", compute="_compute_remaining", store=True)
    last_renewed_date = fields.Date(string="last renewed Date")
    status = fields.Selection(
        selection=[
            ('active', "Active"),
            ('inactive', "Inactive"),
            ('expired', "Expired"),
        ],
        string="Status",
        default='active', compute="_compute_status", store=True)
    renewal_count = fields.Integer(
        string='Renewal Count', compute='_compute_renewal_count')
    utilization_type = fields.Char(
        string='Utilization Type', compute="compute_ut_type")
    rejection_reason = fields.Char(string='Rejection Reason')

    def compute_ut_type(self):
        for rec in self:
            type_names = rec.utilization_line_ids.mapped(
                'coverage_type_id.name')
            rec.utilization_type = ', '.join(type_names)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        template = self.env.ref(
            'insurance.insurance_request_email_template_id', raise_if_not_found=False)
        if template:
            template.send_mail(res.id, force_send=True)
        return res

    @api.depends('end_date')
    def _compute_status(self):
        today = date.today()
        for rec in self:
            if rec.end_date and rec.end_date < today:
                rec.status = "expired"
            else:
                rec.status = "active"

    def make_inactive(self):
        for rec in self:
            rec.status = "inactive"

    def make_active(self):
        for rec in self:
            rec.status = "active"

    def renew_insurance_action(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Renewal',
                'res_model': 'insurance.renewal.history',
                'view_mode': 'form',
                'context': {'default_insurance_id': rec.id},
                'target': 'new'
            }

    def renew_insurance_list_action(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'renewal',
                'res_model': 'insurance.renewal.history',
                'domain': [('insurance_id', '=', rec.id)],
                'view_mode': 'list,form',
                'target': 'current'
            }

    def _compute_renewal_count(self):
        for rec in self:
            rec.renewal_count = self.env['insurance.renewal.history'].search_count(
                [('insurance_id', '=', rec.id)])

    @api.depends('utilization_line_ids.utilized_value')
    def _compute_total_utilization(self):
        for record in self:
            record.total_utilization_amount = sum(
                line.utilized_value for line in record.utilization_line_ids)

    @api.model
    @api.depends('utilization_line_ids')
    def _compute_remaining(self):
        for v in self:
            sum = 0.0
            for insu_id in v.utilization_line_ids:
                sum += insu_id.utilized_value
            v.remaining = v.value - sum

    def action_reject(self):
        for rec in self:
            rec.state = "reject"
            template = self.env.ref(
                'insurance.insurance_rejected_email_template_id', raise_if_not_found=False)
            if template:
                template.send_mail(rec.id, force_send=True)

    def action_submit(self):
        self.state = 'submit'

    def action_approve(self):
        self.state = 'approve'
        template = self.env.ref(
            'insurance.insurance_approval_email_template_id', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    # @api.depends('end_date')
    def update_insurance_expire(self):

        self.state = 'expire'

    @api.model
    def auto_expire_records(self):

        current_date = fields.Date.today()
        records_to_expire = self.search(
            ['&', ('end_date', '<=', current_date), ('state', '=', 'approve')])
        # print('printing....', current_date)
        records_to_expire.write({'state': 'expire'})

    @api.model
    def send_alertt(self):
        today = date.today()
        sender = self.env['res.company'].search(
            [], order='create_date ASC', limit=1)
        if len(sender) > 0:
            expiring_soon_date = today + timedelta(days=30)
            insurances = self.env['employee.insurance'].search(
                [('end_date', '<=', expiring_soon_date), ('end_date', '>=', today)])
            for ch in insurances:
                self.env['mail.mail'].create({
                    'subject': 'Insurance Expire Notification',
                    'email_from': sender.email,
                    # Assuming Via is a user and has an email address
                    'email_to': ch.employee_id.work_email,
                    'body_html': f"Dear {ch.employee_id.name},<br/><br/>"
                    f"Greetings!,<br/><br/>"
                    f"We would like to remind you that your insurance agreement is going to expire on [expiration date]. We would appreciate your guidance on the next steps regarding the renewal or any other actions you would like to take.</br></br>"
                    f"Thank you, and we look forward to your response.</br></br>"
                    f"Best regards</br></br>",
                }).send()

        # current_date = fields.Date.today()
        # expiration_threshold = current_date + timedelta(days=7)
        # expire_soon = self.search([('end_date', '=', expiration_threshold)])
        # # print('printing...')
        # for insurance in expire_soon:
        #     template = self.env.name('insurance.employee_insurance_expire_send_notification')
        #     template.send_mail(insurance.id, force_send=True)


class EmployeeInsurancesLine(models.Model):
    _name = "employee.insurance.line"

    # effective_date = fields.Date(string="Effective Date")
    sequence = fields.Integer(default=10, help="Sequence")
    insurance_id = fields.Many2one(
        'employee.insurance', ondelete='cascade', index=True, copy=False, store=True)
    coverage_type_id = fields.Many2one('coverage.type', string="Utilized Type")
    utilized_value = fields.Float(string="Utilized Amount")
    coverage_value = fields.Float(
        string="Coverage Amount", compute="_compute_coverage_value", store=True)
    remaining_balance = fields.Float(
        string='Remaining Balance', compute='_compute_remaining_balance', store=True)
    total_utilized = fields.Float(
        string='Total Utilized', compute='_compute_total_utilized')
    attachment_ids = fields.Binary(string="Document")

    @api.constrains('remaining_balance')
    def check_remaining_balance(self):
        for rec in self:
            if rec.remaining_balance < 0:
                raise ValidationError("Insufficient Balance")

    @api.depends('utilized_value', 'remaining_balance')
    def _compute_total_utilized(self):
        for rec in self:
            rec.total_utilized = rec.coverage_value - rec.remaining_balance

    @api.model
    @api.depends('coverage_value', 'utilized_value')
    def _compute_remaining_balance(self):
        for record in self:
            old_utilization = self.env['employee.insurance.line'].search(
                [('insurance_id.employee_id', '=', record.insurance_id.employee_id.id), ('coverage_type_id', '=', record.coverage_type_id.id)])
            total = sum(uti.utilized_value for uti in old_utilization)
            record.remaining_balance = record.coverage_value - total

    @api.model
    @api.depends('insurance_id', 'coverage_type_id')
    def _compute_coverage_value(self):

        for rec in self:
            for coverage in self.env['employee.insurance.coverage'].search([('id', '=', rec.insurance_id.name.id)]):
                for co in coverage.insurance_coverage_ids.search(['&',
                                                                  ('employee_id', '=', coverage.employee_id.id), ('coverage_type', '=', rec.coverage_type_id.id)]):
                    rec.coverage_value = co.value


class InsuranceProvider(models.Model):
    _name = "insurance.provider"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Provider Name", required=True)
    contact_name = fields.Char(string="Contact Name", required=True)
    email = fields.Char(string="Email", required=True)
    optional_email = fields.Char(string="Optional Email")
    phone = fields.Char(string="Phon NO", required=True)


class InsuranceType(models.Model):
    _name = "insurance.type"

    name = fields.Char(string="Type of insurance policy")


class EmployeeInsuranceCoverage(models.Model):
    _name = 'employee.insurance.coverage'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference")
    employee_id = fields.Many2one(
        'hr.employee', string="Employee", required=True, store=True)
    category_id = fields.Many2one('insurance.type', string="Policy type")
    provider_id = fields.Many2one(
        'insurance.provider', string="Insurance Provider")
    insurance_coverage_ids = fields.One2many(
        'insurance.coverage.line', 'insurance_coverage_id', copy=True, store=True)
    total_claim = fields.Float(
        string="Total Claim", compute="_compute_total_claim")
    from_date = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    total_annual_premium = fields.Float(string="Total Annual Premium")
    last_renewed_date = fields.Date(string="last renewed Date")
    status = fields.Selection(
        selection=[
            ('active', "Active"),
            ('inactive', "Inactive"),
            ('expired', "Expired"),
        ],
        string="Status",
        default='active', compute="_compute_status", store=True)
    renewal_count = fields.Integer(
        string='Renewal Count', compute='_compute_renewal_count')

    def copy_insurance_employee_action(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Copy',
                'res_model': 'insurance.copy.employee',
                'view_mode': 'form',
                'context': {'default_insurance_id': rec.id},
                'target': 'new'
            }

    # company_id = fields.Many2one('res.company',string="company")

    # @api.model
    # def create(self, vals):
    #     vals['company_id'] =self.env['res.company'].browse(self._context.get('allowed_company_ids'))[0].id
    #     record = super(EmployeeInsuranceCoverage, self).create(vals)
    #     return record

    # @api.model
    # def read(self, fields=None, load='_classic_read'):
    #     user_company_id = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
    #     records = self.search([('create_uid.company_id', 'in', user_company_id.ids)])
    #     return super(EmployeeInsuranceCoverage, records).read(fields=fields, load=load)

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     user_company_id = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
    #     args = args + [('create_uid.company_id', 'in', user_company_id.ids)]
    #     return super(EmployeeInsuranceCoverage, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.depends('date_to')
    def _compute_status(self):
        today = date.today()
        for rec in self:
            if not rec.date_to:
                rec.status = "expired"
            elif rec.date_to and rec.date_to < today:
                rec.status = "expired"
            else:
                rec.status = "active"

    def make_inactive(self):
        for rec in self:
            rec.status = "inactive"

    def make_active(self):
        for rec in self:
            rec.status = "active"

    def renew_insurance_action(self):
        for rec in self:
            original = self.env['insurance.renewal.history'].search(
                [('insurance_id', '=', rec.id), ('status', '=', 'original')])
            if len(original) == 0:
                self.env['insurance.renewal.history'].create({
                    'insurance_id': rec.id,
                    'start_date': rec.from_date,
                    'end_date': rec.date_to,  # Assuming Via is a user and has an email address
                    'status': 'original',  # Assuming Via is a user and has an email address
                    'total_annual_premium': rec.total_annual_premium,
                })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Renewal',
                'res_model': 'insurance.renewal.history',
                'view_mode': 'form',
                'context': {'default_insurance_id': rec.id},
                'target': 'new'
            }

    def renew_insurance_list_action(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'renewal',
                'res_model': 'insurance.renewal.history',
                'domain': [('insurance_id', '=', rec.id)],
                'view_mode': 'list,form',
                'target': 'current'
            }

    def _compute_renewal_count(self):
        for rec in self:
            rec.renewal_count = self.env['insurance.renewal.history'].search_count(
                [('insurance_id', '=', rec.id)])

    @api.model
    def _compute_total_claim(self):
        for rec in self:
            sum = 0.0
            for v in rec.insurance_coverage_ids:
                sum += v.value
            rec.total_claim = sum

    @api.model
    def send_coverage_exp_alert(self):
        today = date.today()
        sender = self.env['res.company'].search(
            [], order='create_date ASC', limit=1)
        if len(sender) > 0:
            expiring_soon_date = today + timedelta(days=30)
            insurances = self.env['employee.insurance.coverage'].search(
                [('date_to', '<=', expiring_soon_date), ('date_to', '>=', today)])
            for ch in insurances:
                for rec in ch.employee_id.company_id.responsible_user_id:
                    self.env['mail.mail'].create({
                        'subject': 'Insurance Renewal Notification',
                        'email_from': sender.email,
                        'email_to': rec.login,  # Assuming Via is a user and has an email address
                        'body_html': f"Hello Dear {rec.name},<br/><br/>Your project{ch.employee_id.company_id.name}, Insurance with Reference {ch.name} is expiring!.<br/><br/>Please renew Your Aggrment With In {(ch.date_to - today).days} days!!<br/><br/>Best regards!!",
                    }).send()


class InsuranceCoverageLine(models.Model):
    _name = 'insurance.coverage.line'
    employee_id = fields.Many2one(
        'hr.employee', related="insurance_coverage_id.employee_id")
    insurance_coverage_id = fields.Many2one(
        'employee.insurance.coverage', string="Coverage", store=True)
    value = fields.Integer(string="Coverage Amount")
    coverage_type = fields.Many2one(
        'coverage.type', string="Coverage Type", required=True)


class CoverageType(models.Model):
    _name = 'coverage.type'

    name = fields.Char(string="Title")


class EmployeeInurance(models.Model):
    _inherit = 'hr.employee'

    insurance_count = fields.Integer(
        string="Insurance count", compute="_compute_insurance_count")

    def _compute_insurance_count(self):
        for rec in self:
            count = self.env['employee.insurance'].search_count(
                [('employee_id', '=', rec.id)])
            rec.insurance_count = count

    def action_open_insurance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'insurance',
            'res_model': 'employee.insurance',
            'domain': [('employee_id', '=', self.id)],
            'view_mode': 'list,form',
            'target': 'current'
        }
