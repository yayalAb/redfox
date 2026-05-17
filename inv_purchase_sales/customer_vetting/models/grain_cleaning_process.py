# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class GrainCleaningProcess(models.Model):
    _name = 'grain.cleaning.process'
    _description = 'Grain Cleaning Process'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        index=True,
        tracking=True,
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    stage_id = fields.Many2one(
        'grain.cleaning.stage',
        string='Stage',
        required=True,
        tracking=True,
        index=True,
        copy=False,
        group_expand='_read_group_stage_ids',
    )
    stage_technical_key = fields.Selection(
        related='stage_id.technical_key',
        string='Stage key',
        store=True,
    )
    line_ids = fields.One2many(
        'grain.cleaning.process.line',
        'process_id',
        string='Lines',
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales order',
        readonly=True,
        copy=False,
        index=True,
    )
    receipt_source_sale_order_id = fields.Many2one(
        'sale.order',
        string='Source sales order (receipt)',
        readonly=True,
        copy=False,
        index=True,
        help='Sales order already linked when this process was created from validating a product-detail receipt.',
    )

    @api.model
    def _read_group_stage_ids(self, groups, domain):
        return groups.search([])

    def _require_lines_for_submit(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Add at least one product line before submitting.'))

    def _set_stage(self, xmlid):
        stage = self.env.ref(xmlid, raise_if_not_found=False)
        if not stage:
            raise UserError(_('Grain cleaning stage configuration is missing (%s).') % xmlid)
        self.write({'stage_id': stage.id})

    def action_submit(self):
        for rec in self:
            if rec.stage_technical_key != 'draft':
                raise UserError(_('Only draft records can be submitted.'))
            rec._require_lines_for_submit()
            rec._set_stage('customer_vetting.grain_cleaning_stage_submitted')
        return True

    def action_review(self):
        for rec in self:
            if rec.stage_technical_key != 'submitted':
                raise UserError(_('Only submitted records can be marked as reviewed.'))
            rec._set_stage('customer_vetting.grain_cleaning_stage_reviewed')
        return True

    def action_approve(self):
        SaleOrder = self.env['sale.order']
        for rec in self:
            if rec.stage_technical_key != 'reviewed':
                raise UserError(_('Only reviewed records can be approved.'))
            if rec.sale_order_id:
                raise UserError(
                    _('A sales order is already linked to this process (%s).')
                    % rec.sale_order_id.display_name
                )
            rec._require_lines_for_submit()
            if rec.receipt_source_sale_order_id:
                so = rec.receipt_source_sale_order_id
                rec.write({'sale_order_id': so.id})
                rec._set_stage('customer_vetting.grain_cleaning_stage_approved')
                rec.message_post(
                    body=_('Linked to existing sales order %s (vetting receipt flow).')
                    % (so._get_html_link(),)
                )
                so.message_post(
                    body=_('Grain cleaning process %s was approved.') % rec._get_html_link()
                )
                continue
            order_line_cmds = []
            for line in rec.line_ids:
                p_uom = line.product_id.uom_id
                req_uom = line.product_uom_id
                if req_uom and req_uom.category_id == p_uom.category_id:
                    uom = req_uom
                else:
                    uom = p_uom
                description = line.name or line.product_id.get_product_multiline_description_sale()
                order_line_cmds.append(
                    (
                        0,
                        0,
                        {
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.product_uom_qty,
                            'product_uom': uom.id,
                            'name': description,
                        },
                    )
                )
            so = SaleOrder.create(
                {
                    'partner_id': rec.partner_id.id,
                    'company_id': rec.company_id.id,
                    'origin': rec.name,
                    'grain_cleaning_process_id': rec.id,
                    'order_line': order_line_cmds,
                }
            )
            rec.write({'sale_order_id': so.id})
            rec._set_stage('customer_vetting.grain_cleaning_stage_approved')
            rec.message_post(body=_('Sales order %s was created.') % so._get_html_link())
            so.message_post(body=_('Created from grain cleaning process %s.') % rec._get_html_link())
        return True

    def action_view_sale_order(self):
        self.ensure_one()
        if not self.sale_order_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_reject(self):
        for rec in self:
            if rec.stage_technical_key not in ('submitted', 'reviewed'):
                raise UserError(_('You can only reject a submitted or reviewed record.'))
            rec._set_stage('customer_vetting.grain_cleaning_stage_rejected')
        return True

    def action_cancel(self):
        for rec in self:
            if rec.stage_technical_key in ('approved', 'rejected', 'cancel'):
                raise UserError(_('This process cannot be cancelled in the current stage.'))
            rec._set_stage('customer_vetting.grain_cleaning_stage_cancelled')
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if rec.stage_technical_key not in ('rejected', 'cancel'):
                raise UserError(_('You can only reset rejected or cancelled records to draft.'))
            rec._set_stage('customer_vetting.grain_cleaning_stage_draft')
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('grain.cleaning.process') or _(
                    'New'
                )
            if not vals.get('stage_id'):
                draft = self.env.ref(
                    'customer_vetting.grain_cleaning_stage_draft', raise_if_not_found=False
                )
                if draft:
                    vals['stage_id'] = draft.id
        return super().create(vals_list)


class GrainCleaningProcessLine(models.Model):
    _name = 'grain.cleaning.process.line'
    _description = 'Grain Cleaning Process Line'

    process_id = fields.Many2one(
        'grain.cleaning.process',
        string='Grain cleaning process',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Service',
        required=True,
        domain=[('sale_ok', '=', True), ('type', '=', 'service')],
    )
    name = fields.Char(string='Description')
    product_uom_qty = fields.Float(
        string='Quantity',
        default=1.0,
        digits='Product Unit of Measure',
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of measure',
        domain="[('category_id', '=', product_uom_category_id)]",
    )
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id',
    )

    @api.constrains('product_id')
    def _check_product_is_service(self):
        for line in self:
            if line.product_id and line.product_id.type != 'service':
                raise ValidationError(
                    _(
                        'Grain cleaning only allows service products (%s is not a service product).'
                    )
                    % line.product_id.display_name
                )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.product_uom_id = line.product_id.uom_id
                line.name = line.product_id.display_name
            else:
                line.product_uom_id = False
                line.name = False
