# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class InheritEmployee(models.Model):
    _inherit = 'hr.employee'

    discipline_count = fields.Integer(compute="_compute_discipline_count")

    def _compute_discipline_count(self):
        all_actions = self.env['disciplinary.action'].read_group([
            ('employee_name', 'in', self.ids),
            ('state', '=', 'action'),
        ], fields=['employee_name'], groupby=['employee_name'])
        mapping = dict([(action['employee_name'][0], action['employee_name_count']) for action in all_actions])
        for employee in self:
            employee.discipline_count = mapping.get(employee.id, 0)


class CategoryDiscipline(models.Model):
    _name = 'discipline.category'
    _description = 'Reason Category'

    # Discipline Categories

    code = fields.Char(string="Code", required=True, help="Category code")
    name = fields.Char(string="Name", required=True, help="Category name")
    category_type = fields.Selection([('disciplinary', 'By Amount'), ('action', 'By Days')],
                                     string="Category Type", help="Choose the category type disciplinary or action")
    description = fields.Text(string="Details", help="Details for this category")
    amount = fields.Float(string="Amount",)


class DisciplinaryAction(models.Model):
    _name = 'disciplinary.action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Disciplinary Action"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('explain', 'Waiting Explanation'),
        ('submitted', 'Waiting Action'),
        ('action', 'Action Validated'),
        ('cancel', 'Cancelled'),

    ], default='draft')

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))

    employee_name = fields.Many2one('hr.employee', string='Employee', required=True, help="Employee name")
    department_name = fields.Many2one('hr.department', string='Department', required=True, help="Department name")
    discipline_reason = fields.Many2one('discipline.category', string='Reason', required=False,
                                        help="Choose a disciplinary reason")
    explanation = fields.Text(string="Explanation by Employee", help='Employee have to give Explanation'
                                                                     'to manager about the discipline of discipline')
    action = fields.Many2one('discipline.category', string="Action",
                             help="Choose an action for this disciplinary action")
    warning_letter = fields.Html(string="Warning Letter")
    suspension_letter = fields.Html(string="Suspension Letter")
    termination_letter = fields.Html(string="Termination Letter")
    warning = fields.Boolean(default=False)
    action_details = fields.Text(string="Action Details", help="Give the details for this action")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments",
                                      help="Employee can submit any documents which supports their explanation")
    note = fields.Text(string="Internal Note")
    category_type = fields.Selection(related="action.category_type", store=True)
    discipline_date = fields.Date(string="Discipline Date", required=True, help="Employee discipline date")
    amount = fields.Float(string='Amount', compute='_compute_amounts_value_by_days', store=True, readonly=False)
    details = fields.Text()
    number_of_days = fields.Float(readonly=True)

    @api.depends('action')
    def _compute_amounts_value_by_days(self):
        for record in self:
            if record.action.category_type == 'disciplinary':
                record.amount = record.action.amount
            elif record.action.category_type == 'action':
                contract = self.env['hr.contract'].sudo().search([('employee_id', '=', record.employee_name.id)],
                                                                 limit=1, order='create_date desc')
                record.amount = (contract.wage / 30) * record.action.amount
                record.number_of_days = record.action.amount



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('disciplinary.action')
        return super(DisciplinaryAction, self).create(vals_list)

    @api.onchange('employee_name')
    def onchange_employee_name(self):
        """ Check the Action Selected"""

        department = self.env['hr.employee'].search([('name', '=', self.employee_name.name)])
        self.department_name = department.department_id.id

        if self.state == 'action':
            raise ValidationError(_('You Can not edit a Validated Action !!'))

    @api.onchange('discipline_reason')
    def onchange_reason(self):
        if self.state == 'action':
            raise ValidationError(_('You Can not edit a Validated Action !!'))

    def assign_function(self):
        for rec in self:
            rec.state = 'explain'

    def submit_function(self):
        for rec in self:
            rec.state = 'submitted'

    def cancel_function(self):
        for rec in self:
            rec.state = 'cancel'

    def set_to_function(self):
        for rec in self:
            rec.state = 'draft'

    def action_function(self):
        for rec in self:
            if not rec.action and self.amount == 0:
                raise ValidationError(_('You have to select an Action !!'))

            if not rec.action_details and self.amount == 0:
                raise ValidationError(_('You have to fill up the Action Details in Action Information !!'))
            rec.state = 'action'


