# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError

class SaleAgreementDocumentWizard(models.TransientModel):
    _name = 'sale.agreement.document.wizard'
    _description = 'Sales Agreement Document Approval Wizard'

    agreement_id = fields.Many2one('sale.agreement', string="Agreement", readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', string="Approval Documents", readonly=True)
    line_ids = fields.One2many(
        'sale.agreement.document.wizard.line',
        'wizard_id',
        string="Approval Documents"
    )

    def action_confirm_and_create_so(self):
        return self.agreement_id.action_do_create_sale_order()
        
class SaleAgreementDocumentWizardLine(models.TransientModel):
    _name = 'sale.agreement.document.wizard.line'
    _description = 'Sales Agreement Document Wizard Line'
    
    wizard_id = fields.Many2one('sale.agreement.document.wizard', required=True, ondelete='cascade')
    attachment_id = fields.Many2one('ir.attachment', string="Document", required=True, readonly=True)
    name = fields.Char(related='attachment_id.name', string="File Name", readonly=True)
    
    def action_view_document(self):
        """
        This method tries to open the internal PDF viewer, but falls back
        to opening in a new tab if the preview view is not found.
        """
        self.ensure_one()
        
        # Try to find the special preview view, but don't raise an error if it's not found.
        preview_view_ref = self.env.ref('mail.view_attachment_form_preview', raise_if_not_found=False)
        
        if preview_view_ref:
            # If we found the view, use it to open the internal PDF viewer.
            return {
                'name': self.name,
                'type': 'ir.actions.act_window',
                'res_model': 'ir.attachment',
                'res_id': self.attachment_id.id,
                'view_mode': 'form',
                'view_id': preview_view_ref.id,
                'target': 'new',
            }
        else:
            # FALLBACK: If the view is missing, open the file in a new browser tab.
            # This prevents the crash.
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.attachment_id.id}?download=false',
                'target': 'new',
            }