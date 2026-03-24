from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('verified', 'Verified'),
            ('authorized', 'Authorized'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )

    submitted_by = fields.Many2one('res.users', string="Submitted By", readonly=True, copy=False)
    verified_by = fields.Many2one('res.users', string="Verified By", readonly=True, copy=False)
    authorized_by = fields.Many2one('res.users', string="Authorized By", readonly=True, copy=False)

    submit_date = fields.Datetime(string="Submit Date", readonly=True, copy=False)
    verify_date = fields.Datetime(string="Verify Date", readonly=True, copy=False)
    authorize_date = fields.Datetime(string="Authorize Date", readonly=True, copy=False)

    def action_submit(self):
        for move in self:
            if move.state != 'draft':
                continue
            move.write({
                'state': 'submitted',
                'submitted_by': self.env.user.id,
                'submit_date': fields.Datetime.now(),
            })
    
    def action_verify(self):
        for move in self:
            if move.state != 'submitted':
                continue
            move.write({
                'state': 'verified',
                'verified_by': self.env.user.id,
                'verify_date': fields.Datetime.now(),
            })
            move.state = 'verified'
    
    def action_authorize(self):
        for move in self:
            if move.state != 'verified':
                continue
            move.write({
                'state': 'authorized',
                'authorized_by': self.env.user.id,
                'authorize_date': fields.Datetime.now(),
            })