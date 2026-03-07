from odoo import models, fields, api


class TrainingRequisition(models.Model):
    _name = 'training.requisition'

    program_name = fields.Char(string='Program Name')
    training_content = fields.Html(string='Training Content')
    training_participants = fields.One2many(
        'participant.lines', 'training_id', string='Training Participants')
    resource_line_ids = fields.One2many(
        'resource.lines', 'training_id', string='Resource Lines')
    estimated_budget = fields.Monetary(
        string='Estimated Budget', compute='_compute_estimated_budget', store=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    training_hours = fields.Float(string='Training Hours')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('verify', 'Verifed'),
        ('approve', 'Approved'),
        ('authorize', 'Authorized'),
        ('planned', 'Planned'),
        ('done', 'Done'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', readonly=True, tracking=True)
    remark = fields.Html(string='Remark')
    creator_id = fields.Many2one(
        'res.users', string='Requestor', default=lambda self: self.env.user, readonly=True)
    requesting_department = fields.Many2one(
        'hr.department', default=lambda self: self.env.user.employee_id.department_id, string='Requesting Department', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True)
    approve_date = fields.Datetime(string='Approved On', readonly=True)
    number_of_trainers = fields.Integer(string='Number of Trainers')
    participants = fields.Char(string='Participants')
    training_place = fields.Char(string='Training Place')

    channel_ids = fields.One2many(
        'slide.channel', 'training_requisition_id', string='Channels')
    channel_count = fields.Integer(
        string='Channel Count', compute='_compute_channel_count')
    authorize_by = fields.Many2one(
        'res.users', string='Authorize By', readonly=True)

    @api.depends('resource_line_ids', 'resource_line_ids.cost')
    def _compute_estimated_budget(self):
        for record in self:
            record.estimated_budget = sum(
                line.cost for line in record.resource_line_ids)

    def action_submit(self):
        self.write({'state': 'in_review'})

    def action_verify(self):
        self.write({'state': 'verify'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_authorize(self):
        self.write({'state': 'authorize', 'authorize_by': self.env.user.id})

    def action_set_to_draft(self):
        self.write({'state': 'draft', 'rejection_reason': ''})

    def action_plan(self):
        self.ensure_one()

        self.write({
            'state': 'planned',
            'approve_date': fields.Datetime.now()
        })

        partner_ids = [
            p.employee_id.related_partner_id.id for p in self.training_participants if p.employee_id.related_partner_id
        ]

        channel_vals = {
            'name': self.program_name,
            'description': self.remark,
            'user_id': self.env.user.id,
            'channel_type': 'training',
            'enroll': 'invite',
            'visibility': 'members',
            'date_start': self.start_date,
            'date_end': self.end_date,
            'training_requisition_id': self.id,
        }
        channel = self.env['slide.channel'].create(channel_vals)

        for line in self.resource_line_ids:
            line.copy(default={'training_id': False, 'channel_id': channel.id})

        if partner_ids:
            channel._action_add_members(
                target_partners=self.env['res.partner'].browse(partner_ids),
                member_status='joined'
            )

    def action_done(self):
        self.write({'state': 'done'})

    @api.depends('channel_ids')
    def _compute_channel_count(self):
        for record in self:
            record.channel_count = len(record.channel_ids)

    def action_view_channels(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'website_slides.slide_channel_action_overview')

        if self.channel_count > 1:
            action['domain'] = [('id', 'in', self.channel_ids.ids)]
        elif self.channel_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.channel_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action


class ParticipantLines(models.Model):
    _name = 'participant.lines'

    training_id = fields.Many2one('training.requisition')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    name = fields.Char(related='employee_id.name', string='Name')
    phone = fields.Char(related='employee_id.phone', string='Phone')
    department_id = fields.Many2one(
        'hr.department', related='employee_id.department_id', string='Department')
    job_id = fields.Many2one(
        'hr.job', related='employee_id.job_id', string='Job')
    company_id = fields.Many2one(
        'res.company', related='employee_id.company_id', string='Company')


class ResourceLines(models.Model):
    _name = 'resource.lines'

    training_id = fields.Many2one(
        'training.requisition', string='Training Requisition', ondelete='cascade')
    channel_id = fields.Many2one(
        'slide.channel', string='Slide Channel', ondelete='cascade')
    name = fields.Char(string='Resource Name', required=True)
    cost = fields.Monetary(string='Cost', compute="_compute_cost")
    currency_id = fields.Many2one(
        'res.currency', string='Currency', related='training_id.currency_id')
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Monetary(string='Unit Price', required=True)

    @api.depends('quantity', 'unit_price')
    def _compute_cost(self):
        for line in self:
            line.cost = line.quantity * line.unit_price
