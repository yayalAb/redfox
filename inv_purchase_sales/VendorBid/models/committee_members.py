from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError

class CommitteeMember(models.Model):
    _name = 'committee.member'

    rfp_id = fields.Many2one('supplies.rfp', string='RFP')
    order_id = fields.Many2one('purchase.order', string="Purchase Order")
    member_id = fields.Many2one('hr.employee', string='Committee Member', required=True)
    related_user_id = fields.Many2one('res.users', related='member_id.user_id', string='System User', store=True)
    name = fields.Char(related='member_id.name', string='Name', store=True)
    role = fields.Selection([
        ('chairperson', 'Chairperson'),
        ('member', 'Member'),
        ('secretary', 'Secretary'),
        ('user_departement', 'User Departement')
    ])
    approval_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending', string='Approval Status')
    approval_date = fields.Date(string='Approval Date')
    can_user_approve = fields.Boolean(
        string='Can Current User Approve',
        compute='_compute_can_user_approve',
        store=False
    )
    rejection_reason = fields.Text(string='Rejection Reason')
    
    @api.depends('related_user_id', 'approval_status', 'order_id.state', 'rfp_id.state')
    def _compute_can_user_approve(self):
        """Check if current user can approve this committee member"""
        current_user = self.env.user
        for rec in self:
            can_approve_order = (
                rec.order_id and
                rec.order_id.state in ('draft', 'sent')
            )
            can_approve_rfp = (
                rec.rfp_id and
                rec.rfp_id.state in ('accepted', 'committee_approving')
            )
            rec.can_user_approve = (
                rec.related_user_id == current_user and
                rec.approval_status == 'pending' and
                (can_approve_order or can_approve_rfp)
            )


    def _check_committee_rights(self):
        """
        Helper to validate Group membership AND Identity.
        """ 
        self.ensure_one()
        current_user = self.env.user
        
        # Check purchase origin from order_id or rfp_id
        purchase_origin = False
        if self.order_id:
            purchase_origin = self.order_id.purchase_origin
        elif self.rfp_id:
            purchase_origin = self.rfp_id.purchase_origin

        if purchase_origin == 'foreign':
            if not current_user.has_group('VendorBid.group_foreign_purchase_committee_member'):
                raise AccessError(_("You do not have the 'Foreign Purchase Committee Member' access rights."))
        elif purchase_origin == 'local':
            if not current_user.has_group('VendorBid.group_local_purchase_committee_member'):
                raise AccessError(_("You do not have the 'Local Purchase Committee Member' access rights."))

        if self.related_user_id != current_user:
            raise UserError(_(
                "You cannot sign off for %s.\n"
                "Only the assigned employee (%s) can approve/reject this line."
            ) % (self.name, self.related_user_id.name or 'No User Linked'))
        
        # Check if order is in correct state
        if self.order_id and self.order_id.state not in ('draft', 'sent'):
            raise UserError(_("You can only approve when the purchase order is in 'Draft' or 'Sent' state."))
        
        # Check if RFP is in correct state
        if self.rfp_id and self.rfp_id.state not in ('accepted', 'committee_approving'):
            raise UserError(_("You can only approve when the RFP is in 'Accepted' or 'Committee Approving' state."))

    def action_committee_approve(self):
        for rec in self:
            rec._check_committee_rights()
            rec.write({
                'approval_status': 'approved',
                'approval_date': fields.Date.today()
            })
            # Check if all members approved and move state
            if rec.order_id:
                rec.order_id._check_and_move_to_committee_approved()
            elif rec.rfp_id:
                rec.rfp_id._check_and_move_to_committee_approving_or_approved()

    def action_committee_reject(self):
        for rec in self:
            rec._check_committee_rights()
            rec.write({
                'approval_status': 'rejected',
                'approval_date': fields.Date.today()
            })

class CommitteeMemberRejectWizard(models.TransientModel):
    _name = 'committee.member.reject.wizard'
    _description = 'Committee Member Reject Wizard'

    # Added the missing comodel 'committee.member'
    committee_member_id = fields.Many2one(
        'committee.member', string='Committee Member', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)
    rejected_by = fields.Many2one(
        'res.users', string='Rejected By', readonly=True, default=lambda self: self.env.user)

    def action_confirm_reject(self):
        self.ensure_one()
        committee = self.committee_member_id

        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason.'))

        if not committee.can_user_approve:
            raise UserError(
                _("You cannot reject this RFP. Please check if you are a committee member with pending approval."))
        
        committee.write({'rejection_reason': self.rejection_reason})
        
        committee.action_committee_reject()
        return True