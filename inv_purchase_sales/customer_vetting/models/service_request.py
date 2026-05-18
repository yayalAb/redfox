# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ServiceRequest(models.Model):
    _name = 'service.request'
    _description = 'Service Request'
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
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('reviewed', 'Reviewed'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        copy=False,
        tracking=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        'service.request.line',
        'request_id',
        string='Lines',
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales order',
        readonly=True,
        copy=False,
        index=True,
    )
    required_filtering_quality = fields.Float(
        string='Required filtering quality',
        tracking=True,
        digits=(16, 4),
    )

    def _require_lines_for_submit(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Add at least one product line before submitting.'))

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            rec._require_lines_for_submit()
            rec.write({'state': 'submitted'})
        return True

    def action_review(self):
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('Only submitted requests can be marked as reviewed.'))
            rec.write({'state': 'reviewed'})
        return True

    def action_approve(self):
        SaleOrder = self.env['sale.order']
        for rec in self:
            if rec.state != 'reviewed':
                raise UserError(_('Only reviewed requests can be approved.'))
            if rec.sale_order_id:
                raise UserError(
                    _('A sales order is already linked to this request (%s).')
                    % rec.sale_order_id.display_name
                )
            rec._require_lines_for_submit()
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
                    'service_request_id': rec.id,
                    'required_filtering_quality': rec.required_filtering_quality,
                    'order_line': order_line_cmds,
                }
            )
            rec.write({'state': 'approved', 'sale_order_id': so.id})
            rec.message_post(
                body=_('Sales order %s was created.') % so._get_html_link()
            )
            so.message_post(
                body=_('Created from service request %s.') % rec._get_html_link()
            )
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
            if rec.state not in ('submitted', 'reviewed'):
                raise UserError(_('You can only reject a submitted or reviewed request.'))
            rec.write({'state': 'rejected'})
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state in ('approved', 'rejected', 'cancel'):
                raise UserError(_('This request cannot be cancelled in the current state.'))
            rec.write({'state': 'cancel'})
        return True

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state not in ('rejected', 'cancel'):
                raise UserError(_('You can only reset rejected or cancelled requests to draft.'))
            rec.write({'state': 'draft'})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('service.request') or _('New')
        return super().create(vals_list)


class ServiceRequestLine(models.Model):
    _name = 'service.request.line'
    _description = 'Service Request Line'

    request_id = fields.Many2one(
        'service.request',
        string='Service request',
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
                    _('Service requests only allow products of type Service (%s is not a service product).')
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
