# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vetting_other_product_id = fields.Many2one(
        'product.template',
        string='Other product',
        domain=[('type', '!=', 'service')],
        help='Related product for vetting. Only goods or combo products (not services).',
    )
    vetting_residue_product_id = fields.Many2one(
        'product.template',
        string='Residue product',
        domain=[('type', '!=', 'service')],
        help='Residue / by-product for vetting. Only goods or combo products (not services).',
    )
    bag_id = fields.Many2one(
        'product.template',
        string='Bag',
        domain=[('type', '!=', 'service')],
        help='Packaging product (bag). Only goods or combo products (not services).',
    )

    @api.constrains('vetting_other_product_id', 'vetting_residue_product_id', 'bag_id')
    def _check_vetting_products(self):
        for tmpl in self:
            if tmpl.vetting_other_product_id:
                if tmpl.vetting_other_product_id.type == 'service':
                    raise ValidationError(
                        _('Other product must not be a service (%s).')
                        % tmpl.vetting_other_product_id.display_name
                    )
                if tmpl.vetting_other_product_id == tmpl:
                    raise ValidationError(_('Other product cannot be the same as this product.'))
            if tmpl.vetting_residue_product_id:
                if tmpl.vetting_residue_product_id.type == 'service':
                    raise ValidationError(
                        _('Residue product must not be a service (%s).')
                        % tmpl.vetting_residue_product_id.display_name
                    )
                if tmpl.vetting_residue_product_id == tmpl:
                    raise ValidationError(_('Residue product cannot be the same as this product.'))
            if tmpl.bag_id:
                if tmpl.bag_id.type == 'service':
                    raise ValidationError(
                        _('Bag must not be a service (%s).') % tmpl.bag_id.display_name
                    )
                if tmpl.bag_id == tmpl:
                    raise ValidationError(_('Bag cannot be the same as this product.'))
