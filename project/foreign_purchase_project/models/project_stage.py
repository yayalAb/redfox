from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectStage(models.Model):
    _inherit = 'project.project.stage'

    is_foreign_purchase = fields.Boolean(
        string="Is Foreign Purchase", default=False)
    is_bill = fields.Boolean(string="Is Bill")

    accountable_user_ids = fields.Many2many(
        'res.users',
        string='Accountable Persons',
        help="Only these users are allowed to move projects out of this stage."
    )


class ProjectProject(models.Model):
    _inherit = 'project.project'

    purchase_order_ids = fields.One2many(
        'purchase.order', 'project_id', string='Purchase Order')
    stage_is_bill = fields.Boolean(
        related='stage_id.is_bill', string="Stage Is Bill", readonly=True)

    @api.constrains('purchase_order_ids')
    def _check_purchase_order(self):
        for project in self:
            # Check if more than one PO is attached
            if len(project.purchase_order_ids) > 1:
                raise ValidationError(
                    _("You can only attach one Purchase Order per project."))

    def write(self, vals):
        if 'stage_id' in vals:
            for project in self:
                current_stage = project.stage_id

                if current_stage.accountable_user_ids:
                    if self.env.user not in current_stage.accountable_user_ids and not self.env.is_admin():
                        authorized_names = ', '.join(current_stage.accountable_user_ids.mapped('name'))
                        
                        raise UserError(_(
                            "You are not authorized! Only the following users can move projects out of the '%(stage)s' stage:\n%(users)s"
                        ) % {
                            'users': authorized_names,
                            'stage': current_stage.name
                        })
                        
        return super(ProjectProject, self).write(vals)

    def action_open_landed_cost_wizard(self):
        self.ensure_one()
        return {
            'name': _('Add Landed Cost'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.landed.cost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_project_id': self.id},
        }