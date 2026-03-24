# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class SaleAgreement(models.Model):
    _inherit = 'sale.agreement'

    code = fields.Char(string="Contract Number", required=True,
                       default=lambda self: _('New'), readonly=True, copy=False)
    agreement_category = fields.Selection([
        ('product_sale', 'Product Sale'),
        ('maintenance', 'Maintenance'),
        ('test', 'Test')
    ])
    name = fields.Char(string='Contract Name')
    country_of_origin_id = fields.Many2one(
        'res.country', string='Country of Origin')
    year_of_manufacturing = fields.Char(string='Year of Manufacturing')
    due_date = fields.Date(string='Due Date')
    method_of_payment = fields.Selection([
        ('100_payment', '100% Payment'),
        ('75_payment', '75% Payment'),
        ('50_payment', '50% Payment'),
        ('30_payment', '30% Payment'),
        ('25_payment', '25% Payment'),
        ('10_payment', '10% Payment'),
    ], string='Pre Payment'
    )
    production_period = fields.Char(string='Production Period')
    customer_type = fields.Selection([
        ('private', 'Private   '),
        ('corporate', 'Corporate'),
    ], string='Customer Type'
    )
    source_from = fields.Selection([
        ('tender', 'Tender'),
        ('direct', 'Direct'),
        ('contract', 'Contract Request'),
    ], string="Source From")
    # mrp_production_ids = fields.One2many(
    #     'mrp.production',
    #     'agreement_id',
    #     string='Manufacturing Orders'
    # )
    # mrp_count = fields.Integer(
    #     string="Manufacturing Count",
    #     compute='_compute_mrp_count'
    # )
    # service_request_ids = fields.One2many(
    #     'service.request',
    #     'agreement_id',
    #     string='Service Requests'
    # )
    # service_request_count = fields.Integer(
    #     string="Service Request Count",
    #     compute='_compute_service_request_count'
    # )
    # client_maintenance_ids = fields.One2many(
    #     'mrp.production', 'agreement_id', string='Client Maintenance')
    # client_maintenance_count = fields.Integer(
    #     string="client Maintenance Count",
    #     compute='_compute_client_maintenance_count'
    # )
    # client_testing_count = fields.Integer(
    #     string="Client Testing Count", compute='_compute_client_testing_count')

    # rfp_ids = fields.One2many(
    #     'supplies.rfp',
    #     'agreement_id',
    #     string='Purchase Requests'
    # )
    # rfp_count = fields.Integer(
    #     string="RFP Count",
    #     compute='_compute_rfp_count'
    # )
    cip_count = fields.Integer(compute='_compute_cip_count')
    contract_request_id = fields.Many2one(
        'contract.request', string='Contract Request')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                sequence_code = self.env['ir.sequence'].next_by_code(
                    'sale.agreement') or _('New')
                vals['code'] = sequence_code
        return super().create(vals_list)

    def action_confirm(self):
        for agreement in self:
            if not agreement.line_ids:
                raise ValidationError(
                    _("Please add at least one product to create a contract agreement."))
        return super(SaleAgreement, self).action_confirm()

    # def unlink(self):
    #     for agreement in self:
    #         if agreement.state != 'draft':
    #             raise ValidationError(
    #                 _("You can only delete agreements that are in the Draft state."))
    #     return super(SaleAgreement, self).unlink()

    # def _compute_mrp_count(self):
    #     for agreement in self:
    #         agreement.mrp_count = len(agreement.mrp_production_ids)

    # @api.depends('mrp_production_ids')
    # def _compute_client_maintenance_count(self):
    #     for agreement in self:
    #         maintenance_mos = agreement.mrp_production_ids.filtered(
    #             lambda mo: mo.production_type == 'maintenance'
    #         )
    #         agreement.client_maintenance_count = len(maintenance_mos)

    # @api.depends('mrp_production_ids')
    # def _compute_client_testing_count(self):
    #     for agreement in self:
    #         testing_mos = agreement.mrp_production_ids.filtered(
    #             lambda mo: mo.production_type == 'test'
    #         )
    #         agreement.client_testing_count = len(testing_mos)

    # def action_view_manufacturing_orders(self):
    #     self.ensure_one()
    #     action = {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Manufacturing Orders',
    #         'res_model': 'mrp.production',
    #         'domain': [('id', 'in', self.mrp_production_ids.ids)],
    #         'context': {
    #             'default_agreement_id': self.id,
    #             'default_origin': self.name,
    #         }
    #     }

    #     if len(self.mrp_production_ids) == 1:
    #         action['res_id'] = self.mrp_production_ids.id
    #         action['view_mode'] = 'form'
    #     else:
    #         action['view_mode'] = 'list,form'
    #     return action

    # def action_create_manufacturing_order(self):
    #     self.ensure_one()
    #     if self.state != 'confirmed':
    #         raise ValidationError(
    #             _("Manufacturing Orders can only be created from a confirmed agreement."))
    #     if not self.line_ids:
    #         raise ValidationError(
    #             _("You must have at least one product line to create a Manufacturing Order."))

    #     manufacture_route = self.env.ref(
    #         'mrp.route_warehouse0_manufacture', raise_if_not_found=False)
    #     if not manufacture_route:
    #         raise ValidationError(
    #             _("The 'Manufacture' route could not be found. Please ensure the Manufacturing module is correctly installed."))

    #     mo_created_count = 0
    #     for line in self.line_ids:
    #         if manufacture_route not in line.product_id.route_ids:
    #             continue

    #         if self.agreement_category == 'test':
    #             production_type = 'test'
    #         elif self.agreement_category == 'product_sale':
    #             production_type = 'manufacturing'
    #         self.env['mrp.production'].create({
    #             'product_id': line.product_id.id,
    #             'product_uom_id': line.uom_id.id,
    #             'product_qty': line.quantity - line.manufactured_qty,
    #             'origin': self.name,
    #             'agreement_id': self.id,
    #             'production_type': production_type,
    #         })
    #         mo_created_count += 1

    #     if mo_created_count == 0:
    #         raise ValidationError(
    #             _("No products with the 'Manufacture' route were found on this agreement."))

    #     return self.action_view_manufacturing_orders()

    # def _compute_service_request_count(self):
    #     for agreement in self:
    #         agreement.service_request_count = len(
    #             agreement.service_request_ids)

    # def action_view_service_requests(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Service Requests',
    #         'res_model': 'service.request',
    #         'view_mode': 'list,form',
    #         'domain': [('id', 'in', self.service_request_ids.ids)],
    #         'context': {'default_agreement_id': self.id}
    #     }

    # def action_create_service_request(self):
    #     self.ensure_one()
    #     first_service_line = self.line_ids[0]

    #     context = {
    #         'default_agreement_id': self.id,
    #         'default_name': self.name,
    #         'default_date': self.signature_date,
    #         'default_product_id': first_service_line.product_id.id,
    #         'default_quantity': first_service_line.quantity,
    #         'default_requesting_person': self.partner_id.name,
    #     }
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Create Service Request',
    #         'res_model': 'service.request',
    #         'view_mode': 'form',
    #         'target': 'current',
    #         'context': context,
    #     }

    # def action_create_sale_order(self):
    #     """
    #     This method gathers quality documents from relevant MOs
    #     and opens the approval wizard.
    #     """
    #     self.ensure_one()
    #     if self.state != "approved":
    #         raise ValidationError(
    #             _("Only approved agreements can create sale orders."))

    #     lines_with_available_qty = self.line_ids.filtered(
    #         lambda l: l.manufactured_qty > l.ordered_qty)

    #     # if not lines_with_available_qty:
    #     #     raise ValidationError(
    #     #         _("There are no manufactured quantities available to create a sales order. Please complete or partially record production in the Manufacturing Orders first."))

    #     relevant_mos = self.mrp_production_ids.filtered(
    #         lambda mo: mo.state not in ['draft', 'cancel']
    #     )

    #     # all_attachments = self.env['ir.attachment'].browse()
    #     # for mo in relevant_mos:
    #     #     all_attachments |= mo.quality_document_ids

    #     # # if not all_attachments:
    #     # #     raise ValidationError(
    #     # #         _("No Quality Approval Documents have been uploaded for the relevant Manufacturing Orders. Please upload them before creating a Sales Order."))

    #     # wizard_lines = []
    #     # for att in all_attachments:
    #     #     wizard_lines.append((0, 0, {'attachment_id': att.id}))

    #     # # Create the main wizard record with the lines
    #     # wizard = self.env['sale.agreement.document.wizard'].create({
    #     #     'agreement_id': self.id,
    #     #     'line_ids': wizard_lines,
    #     # })

    #     # # Return an action to open the wizard in a pop-up
    #     # return {
    #     #     'name': _('Approve Quality Documents'),
    #     #     'type': 'ir.actions.act_window',
    #     #     'res_model': 'sale.agreement.document.wizard',
    #     #     'res_id': wizard.id,
    #     #     'view_mode': 'form',
    #     #     'target': 'new',
    #     # }

    #     return self.action_do_create_sale_order()

    # def action_do_create_sale_order(self):
    #     """
    #     This new method contains the actual SO creation logic.
    #     It is called by the wizard's confirm button.
    #     """
    #     self.ensure_one()
    #     lines_to_process = self.line_ids.filtered(
    #         lambda l: l.quantity > l.ordered_qty)

    #     sale_order = self.env["sale.order"].create({
    #         "partner_id": self.partner_id.id, "company_id": self.company_id.id,
    #         "origin": self.name, "date_order": fields.Date.today(),
    #         "agreement_id": self.id,
    #         "state": "order_submit"
    #     })

    #     for line in lines_to_process:
    #         remaining_qty_to_order = line.quantity - line.ordered_qty
    #         if remaining_qty_to_order > 0:
    #             self.env["sale.order.line"].create({
    #                 "order_id": sale_order.id, "product_id": line.product_id.id,
    #                 "name": line.product_id.name, "product_uom_qty": remaining_qty_to_order,
    #                 "product_uom": line.uom_id.id, "price_unit": line.unit_price,
    #                 "tax_id": [(6, 0, line.tax_ids.ids)],
    #             })

    #     self.line_ids._compute_ordered_qty()

    #     return {
    #         "type": "ir.actions.act_window", 
    #         "res_model": "sale.order",
    #         "res_id": sale_order.id, 
    #         "view_mode": "form",
    #         "target": "current",
    #     }

    # def action_create_service_request(self):
    #     self.ensure_one()
    #     if self.state not in ('approved'):
    #         raise ValidationError(
    #             _("Manufacturing Orders can only be created from an agreement in approved state."))
    #     if not self.line_ids:
    #         raise ValidationError(
    #             _("You must have at least one product line to create a service request."))

    #     manufacture_route = self.env.ref(
    #         'mrp.route_warehouse0_manufacture', raise_if_not_found=False)
    #     if not manufacture_route:
    #         raise ValidationError(
    #             _("The 'Manufacture' route could not be found. Please ensure the Manufacturing module is correctly installed."))

    #     sr_created_count = 0
    #     for line in self.line_ids:
    #         if manufacture_route not in line.product_id.route_ids:
    #             continue

    #         self.env['service.request'].create({
    #             'product_id': line.product_id.id,
    #             'quantity': line.quantity - line.manufactured_qty,
    #             'agreement_id': self.id,
    #             'name': self.name,
    #             'date': self.signature_date,
    #             'requesting_department': self.env.user.department_id.id,
    #         })
    #         sr_created_count += 1

    #     if sr_created_count == 0:
    #         raise ValidationError(
    #             _("No products with the 'Manufacture' route were found on this agreement."))

    #     return self.action_view_service_requests()

    # def action_view_client_maintenance(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Client Maintenance',
    #         'res_model': 'mrp.production',
    #         'view_mode': 'list,form',
    #         'domain': [('agreement_id', '=', self.id)],
    #     }

    # def action_view_client_testing(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Client Testing',
    #         'res_model': 'mrp.production',
    #         'view_mode': 'list,form',
    #         'domain': [('agreement_id', '=', self.id)],
    #     }

    # def _compute_rfp_count(self):
    #     for rec in self:
    #         rec.rfp_count = len(rec.rfp_ids)

    # def action_view_rfps(self):
    #     self.ensure_one()
    #     return {
    #         'name': _('Purchase Requests'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'supplies.rfp',
    #         'view_mode': 'list,form',
    #         'domain': [('agreement_id', '=', self.id)],
    #         'context': {'default_agreement_id': self.id}
    #     }

    # def action_create_purchase_request(self):
    #     self.ensure_one()

    #     if self.state != 'approved':
    #         raise ValidationError(
    #             _("You can only create Purchase Requests for approved agreements."))

    #     if not self.line_ids:
    #         raise ValidationError(
    #             _("No product lines found to create a purchase request."))

    #     all_category = self.env.ref(
    #         'product.product_category_all', raise_if_not_found=False)

    #     if not all_category:
    #         all_category = self.env['product.category'].search(
    #             [('parent_id', '=', False)], limit=1)

    #     if not all_category:
    #         raise UserError(
    #             _("Could not find a Root Product Category (e.g., 'All'). Please configure product categories."))

    #     rfp_vals = {
    #         'agreement_id': self.id,
    #         'product_category_id': all_category.id,  # This allows ANY product to be added
    #         'purchase_origin': 'local',
    #         'purchase_type': 'direct',
    #         'purpose': f"Materials for Contract: {self.code} - {self.name or ''}",
    #         'project_id': self.env.context.get('default_project_id') or False,
    #         'start_date': fields.Date.today(),
    #         'requested_date': fields.Datetime.now(),
    #     }

    #     # 4. Prepare Product Lines
    #     rfp_lines_vals = []
    #     for line in self.line_ids:
    #         if line.product_id.type == 'service':
    #             continue
    #         qty_to_request = line.quantity - line.manufactured_qty

    #         if qty_to_request <= 0:
    #             continue

    #         rfp_lines_vals.append((0, 0, {
    #             'product_id': line.product_id.id,
    #             'product_qty': qty_to_request,
    #             'unit_price': 0.0,
    #             'description': f"{line.product_id.name} (Ref: {self.code})",
    #         }))

    #     if not rfp_lines_vals:
    #         raise UserError(
    #             _("All products in this agreement are already manufactured or have 0 quantity required."))

    #     rfp_vals['product_line_ids'] = rfp_lines_vals
    #     self.env['supplies.rfp'].create(rfp_vals)

    #     return self.action_view_rfps()

    def _compute_cip_count(self):
        for rec in self:
            rec.cip_count = self.env['cip.request'].search_count(
                [('agreement_id', '=', rec.id)])

    def action_view_cip_requests(self):
        return {
            'name': _('CIP Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'cip.request',
            'view_mode': 'tree,form',
            'domain': [('agreement_id', '=', self.id)],
            'context': {'default_agreement_id': self.id}
        }

    def action_create_cip_request(self):
        self.ensure_one()

        if self.state != 'approved':
            raise UserError(
                _("CIP Requests can only be created for approved agreements."))

        cip_line_vals = []
        for line in self.line_ids:
            qty_offered = line.manufactured_qty - line.tested_qty

            if qty_offered <= 0:
                continue

            cip_line_vals.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity_total': line.quantity,        # Amount agreed with customer
                'quantity_accepted': line.tested_qty,   # Amount already accepted/tested
                'quantity_offered': qty_offered,        # Quantity to be tested now
            }))

        if not cip_line_vals:
            raise UserError(
                _("There are no manufactured products available for inspection (Quantity Offered is 0)."))

        cip_request = self.env['cip.request'].create({
            'name': _('CIP/%s/%s') % (self.code, fields.Date.today()),
            'agreement_id': self.id,
            'contract_name': self.name,
            'contract_date': self.create_date,  # Or your specific signature field
            'supplier_name': self.company_id.name,
            'state': 'draft',
            'line_ids': cip_line_vals,
        })

        return {
            'name': _('CIP Request'),
            'view_mode': 'form',
            'res_model': 'cip.request',
            'res_id': cip_request.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


# class AgreementLine(models.Model):
#     _inherit = "agreement.line"

#     manufactured_qty = fields.Integer(
#         compute="_compute_manufactured_qty",
#         store=True)
#     tested_qty = fields.Integer(
#         compute="_compute_manufactured_qty",
#         store=True
#     )

#     @api.depends('agreement_id.mrp_production_ids.state',
#                  'agreement_id.mrp_production_ids.product_qty',
#                  'agreement_id.mrp_production_ids.elpa_approved')
#     def _compute_manufactured_qty(self):
#         for line in self:
#             related_mos = line.agreement_id.mrp_production_ids.filtered(
#                 lambda mo: mo.product_id == line.product_id and mo.state not in [
#                     'draft', 'cancel', 'confirmed', 'progress', 'to_close']
#             )
#             line.manufactured_qty = sum(related_mos.mapped('product_qty'))

#             tested_mos = related_mos.filtered(lambda mo: mo.elpa_approved)
#             line.tested_qty = sum(tested_mos.mapped('product_qty'))
