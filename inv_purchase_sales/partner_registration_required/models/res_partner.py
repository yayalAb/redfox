# -*- coding: utf-8 -*-
from odoo import _, api, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _requires_registration_fields(self):
        """Top-level customer/vendor records (not child contacts or addresses)."""
        self.ensure_one()
        return not self.parent_id

    @api.constrains('vat', 'phone', 'parent_id')
    def _check_registration_required_fields(self):
        for partner in self:
            if not partner._requires_registration_fields():
                continue
            if not (partner.vat or '').strip():
                raise ValidationError(_(
                    'Tax ID is required when registering a customer or vendor.'
                ))
            if not (partner.phone or '').strip():
                raise ValidationError(_(
                    'Phone is required when registering a customer or vendor.'
                ))
