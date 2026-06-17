# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class CustomerVettingCreateDeliveryWizard(models.TransientModel):
    _name = 'customer.vetting.create.delivery.wizard'
    _description = 'Create customer vetting delivery order'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales order',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    line_ids = fields.One2many(
        'customer.vetting.create.delivery.wizard.line',
        'wizard_id',
        string='Products to deliver',
    )

    def action_create_delivery(self):
        self.ensure_one()
        selected = self.line_ids.filtered(lambda l: l.selected and l.product_uom_qty > 0)
        if not selected:
            raise UserError(
                _('Select at least one product with a quantity greater than zero.')
            )
        for line in selected:
            if (
                float_compare(
                    line.product_uom_qty,
                    line.available_qty,
                    precision_rounding=line.product_uom_id.rounding,
                )
                > 0
            ):
                raise UserError(
                    _(
                        'Quantity to deliver for %(product)s cannot exceed the available '
                        'quantity (%(available)s %(uom)s).',
                        product=line.product_id.display_name,
                        available=line.available_qty,
                        uom=line.product_uom_id.name,
                    )
                )
        line_specs = [
            {
                'product_id': line.product_id,
                'product_uom_id': line.product_uom_id,
                'product_uom_qty': line.product_uom_qty,
                'mrp_production_ids': line.mrp_production_ids,
            }
            for line in selected
        ]
        picking = self.sale_order_id._customer_vetting_create_delivery_picking(line_specs)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Delivery order'),
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }


class CustomerVettingCreateDeliveryWizardLine(models.TransientModel):
    _name = 'customer.vetting.create.delivery.wizard.line'
    _description = 'Customer vetting delivery wizard line'

    wizard_id = fields.Many2one(
        'customer.vetting.create.delivery.wizard',
        required=True,
        ondelete='cascade',
    )
    selected = fields.Boolean(string='Deliver', default=True)
    mrp_production_ids = fields.Many2many(
        'mrp.production',
        string='Manufacturing orders',
        readonly=True,
    )
    line_type = fields.Selection(
        [
            ('finished', 'Finished product'),
            ('byproduct', 'By-product'),
            ('residue', 'Residue'),
        ],
        string='Type',
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        readonly=True,
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of measure',
        required=True,
        readonly=True,
    )
    available_qty = fields.Float(
        string='Available quantity',
        digits='Product Unit of Measure',
        readonly=True,
    )
    product_uom_qty = fields.Float(
        string='Quantity to deliver',
        digits='Product Unit of Measure',
        required=True,
    )
