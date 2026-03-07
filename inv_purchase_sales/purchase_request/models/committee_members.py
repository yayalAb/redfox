from odoo import models, fields
from odoo.exceptions import UserError, AccessError

class CommitteeMember(models.Model):
    _name = 'committee.member'

    rfp_id = fields.Many2one('supplies.rfp', string='RFP', required=True)
    member_id = fields.Many2one('hr.employee', string='Committee Member', required=True)
    related_user_id = fields.Many2one('res.users', related='member_id.user_id', string='System User', store=True)
    name = fields.Char(related='member_id.name', string='Name', store=True)
    role = fields.Selection([
        ('chairperson', 'Chairperson'),
        ('member', 'Member'),
    ])
    approval_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending', string='Approval Status')


    def _check_committee_rights(self):
        """
        Helper to validate Group membership AND Identity.
        """ 
        self.ensure_one()
        current_user = self.env.user

        if self.rfp_id.purchase_origin == 'foreign':
            if not current_user.has_group('VendorBid.group_foreign_purchase_committee_member'):
                raise AccessError(_("You do not have the 'Foreign Purchase Committee Member' access rights."))
        else:
            if not current_user.has_group('VendorBid.group_local_purchase_committee_member'):
                raise AccessError(_("You do not have the 'Local Purchase Committee Member' access rights."))

        if self.related_user_id != current_user:
            raise UserError(_(
                "You cannot sign off for %s.\n"
                "Only the assigned employee (%s) can approve/reject this line."
            ) % (self.name, self.related_user_id.name or 'No User Linked'))
        

    def action_committee_approve(self):
        for rec in self:
            rec._check_committee_rights()
            rec.write({
                'approval_status': 'approved',
                'approval_date': fields.Datetime.now()
            })

    def action_committee_reject(self):
        for rec in self:
            rec._check_committee_rights()
            rec.write({
                'approval_status': 'rejected',
                'approval_date': fields.Datetime.now()
            })