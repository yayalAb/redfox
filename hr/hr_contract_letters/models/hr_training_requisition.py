# -*- coding: utf-8 -*-
from odoo import models, api


class TrainingRequisition(models.Model):
    _inherit = 'training.requisition'

    def action_print_send_training_invitation(self):
        """Open wizard to print/send training invitation"""
        self.ensure_one()
        return {
            'name': 'Print/Send Training Invitation',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.training.invitation.send.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_training_requisition_id': self.id,
            }
        }
