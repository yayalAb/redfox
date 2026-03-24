# -*- coding: utf-8 -*-
from odoo import models, fields, api,  _
from odoo.exceptions import ValidationError, UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_category = fields.Selection([
        ('product_sale', 'Product Sale'),
        ('maintenance', 'Maintenance'),
        ('test', 'Test')
    ])
    
    # ADD THIS LINK FIELD (Inverse of sale_order_id in Payment Request)
    payment_request_ids = fields.One2many('payment.request', 'sale_order_id', string='Payment Requests')
    payment_request_count = fields.Integer(string="Payment Requests", compute='_compute_payment_request_count')

    report_remark = fields.Text(string='Report Remark', 
                                help="Text to appear in the Remark section of the printout")
    partner_tin = fields.Char(string='TIN', help="Tax Identification Number")
    # Link to the actual agreement record (for selection)
    agreement_id = fields.Many2one('sale.agreement', string="Source Agreement")
    # The text field that prints on report (Editable)
    contract_ref = fields.Char(string='Contract No', help="Reference to the Agreement/Contract")

    mrp_ids = fields.Many2one('mrp.production', string='Manufacturing Orders')
    mrp_count = fields.Integer(
        string="MRP Count", compute='_compute_mrp_count')
    state = fields.Selection(
        selection=[
            ('draft', "Quotation Draft"),
            ('quotation_submit', "Quotation Submitted"),
            ('quotation_review', "Quotation Reviewed"),
            ('quotation_approve', "Quotation Approved"),
            ('quotation_refuse', "Quotation Refused"),
            ('sent', "Quotation Sent"),
            ('order_submit', 'Order Submitted'),
            ('order_review', 'Order Reviewed'),
            ('sale', "Sales Order"),
            ('cancel', "Cancelled"),
        ], string="Status",  readonly=True, 
        copy=False, index=True,
        tracking=3, default='draft')

    order_type = fields.Selection([
        ('quotation', 'Quotation'), ('order', 'Order')
    ], default='quotation', string='Order Type')


        #  EDITABLE FIELDS FOR REPORT
    partner_tin = fields.Char(string='TIN', help="Tax Identification Number")
    
    agreement_id = fields.Many2one('sale.agreement', string="Source Agreement")
    contract_ref = fields.Char(string='Contract No', help="Reference to the Agreement/Contract")

    # SIGNATURE FIELDS (Auto-captured)
    prepared_by_id = fields.Many2one('res.users', string='Prepared By', readonly=True)
    prepared_date = fields.Date(string='Prepared Date', readonly=True)
    
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Date(string='Approved Date', readonly=True)

    @api.constrains('sale_category')
    def _check_sale_category(self):
        for order in self:
            if order.state == 'order_submit' and not order.sale_category:
                raise ValidationError("please select sale category before submitting order.")
    
    @api.onchange('partner_id')
    def _onchange_partner_id_tin(self):
        """
        Trigger: When Customer is selected.
        Action: Fills the 'partner_tin' field with the customer's VAT/TIN.
        """
        if self.partner_id:
            # 'vat' is the standard Odoo field for Tax ID
            self.partner_tin = self.partner_id.vat or ""
        else:
            self.partner_tin = ""

    @api.onchange('agreement_id')
    def _onchange_agreement_id_contract(self):
        """
        Trigger: When an Agreement is selected from the dropdown.
        Action: Fills the 'contract_ref' field with the Agreement Code.
        """
        if self.agreement_id:
            # Prefers the Agreement Code, otherwise uses Name
            self.contract_ref = self.agreement_id.code or self.agreement_id.name
        else:
            self.contract_ref = ""
            
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'sale.quotation') or _('New')
        return super(SaleOrder, self).create(vals_list)

    def action_quotation_submit(self):
        for order in self:
            order.write({
                'state': 'quotation_submit',
                'prepared_by_id': self.env.user.id,
                'prepared_date': fields.Date.today()
            })

    def action_quotation_review(self):
        for order in self:
            order.write({'state': 'quotation_review'})

    def action_quotation_approve(self):
        for order in self:
            order.write({'state': 'quotation_approve'})

    def action_quotation_reject(self):
        for order in self:
            order.write({'state': 'quotation_refuse'})

    def action_quotation_reset_to_draft(self):
        for order in self:
            order.write({'state': 'draft'})
            
    def action_submit_order(self):
        for order in self:
            name = self.env['ir.sequence'].next_by_code('sale.order') or _('New')
            order.write({
                'name': name, 
                'state': 'order_submit', 
                'order_type': 'order',
                # Capture again for the official Order phase
                'prepared_by_id': self.env.user.id,
                'prepared_date': fields.Date.today()
            })
            
    def action_review_order(self):
        for order in self:
            order.write({'state': 'order_review'})

    def action_confirm(self):
        for order in self:
            if not order.order_line:
                raise ValidationError(
                    _("You cannot confirm a sales order without any product lines."))
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            order.write({
                'approved_by_id': self.env.user.id,
                'approved_date': fields.Date.today()
            })
        return res

    def _confirmation_error_message(self):
        """ Return whether order can be confirmed or not if not then returm error message. """
        self.ensure_one()
        if self.state not in {'order_review'}:
            return _("Some orders are not in a state requiring confirmation.")
        if any(
            not line.display_type
            and not line.is_downpayment
            and not line.product_id
            for line in self.order_line
        ):
            return _("A line on these orders missing a product, you cannot confirm it.")

        return False

    # ADD THE payment request COMPUTE METHOD
    @api.depends('payment_request_ids')
    def _compute_payment_request_count(self):
        for order in self:
            order.payment_request_count = len(order.payment_request_ids)

    # 3. Action Button Logic
    def action_view_payment_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Requests',
            'res_model': 'payment.request',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id}
        }


        
    def _compute_mrp_count(self):
        for record in self:
            record.mrp_count = self.env['mrp.production'].search_count(
                [('origin', '=', record.name)])

    def action_create_mrp(self):
        """
        Creates a separate Manufacturing Order for each Sales Order Line
        ONLY if the product has the 'Manufacture' route configured.
        """
        mrp_production = self.env['mrp.production']
        manufacture_route = self.env.ref('mrp.route_warehouse0_manufacture')

        for order in self:
            created_mrps = False

            for line in order.order_line:
                # 1. Skip sections/notes or products with 0 qty
                if line.display_type or line.product_uom_qty <= 0:
                    continue

                product_routes = line.product_id.route_ids | line.product_id.categ_id.route_ids

                if manufacture_route in product_routes:

                    mrp_vals = {
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_uom_id': line.product_uom.id,
                        'origin': order.name,
                        'company_id': order.company_id.id,
                    }

                    mrp_production.create(mrp_vals)
                    created_mrps = True

            if not created_mrps:
                raise UserError(
                    _("No lines found with the 'Manufacture' route to create orders."))

        # Redirect to the view showing all created MOs
        return self.action_view_mrp()

    def action_view_mrp(self):
        """
        View function: Shows list of MOs if multiple, or form view if only one.
        """
        self.ensure_one()
        domain = [('origin', '=', self.name)]
        mrp_ids = self.env['mrp.production'].search(domain).ids

        action = {
            'name': _('Manufacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'domain': domain,
            'context': {'default_origin': self.name},
        }

        if len(mrp_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = mrp_ids[0]
        else:
            action['view_mode'] = 'list,form'

        return action
