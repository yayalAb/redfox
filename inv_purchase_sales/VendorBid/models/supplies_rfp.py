from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict


class SuppliesRfp(models.Model):

    _name = 'supplies.rfp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Purchase Request'
    _rec_name = 'rfp_number'
    _order = 'requested_date desc'

    rfp_number = fields.Char(
        string='RFP Number', index=True, default='New')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('initial_verfayed', 'verfied'),
        ('approved', 'Approved'),
        ('evaluation', 'Evaluation'),
        ('accepted', 'Accepted'),
        ('committee_approving', 'Committee Approving'),
        ('committee_approved', 'Committee Approved'),
        ('verfayed', 'Verfied'),
        ('f_approved', 'Final Approved'),
        ('ordered', 'Ordered'),
        ('re_evaluated', 'Re-Evaluated'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], string='Status', index=True, tracking=True, default='draft')
    purchase_origin = fields.Selection([
        ('local', 'Local'), ('foreign', 'Foreign')],
        string='Purchase Origin', required=True, default='local')
    purchase_type = fields.Selection([
        ('petty_cash', 'Petty Cash'),
        ('bid', 'Bid'),
        ('direct', 'Direct'),
        ('proforma', 'Proforma Invoice'),

    ], string='Purchase Method', default='proforma')
    product_line_ids = fields.One2many(
        'supplies.rfp.product.line', 'rfp_id', string='Product Lines')
    rfq_ids = fields.One2many('purchase.order', 'rfp_id',
                              string='Quotations', domain=lambda self: self._get_rfq_domain())
    rfq_count = fields.Integer(
        string='Number of RFQs', compute='_compute_rfq_count', store=False)
    rfq_line_ids = fields.One2many('purchase.order.line', 'rfp_id',
                                   compute='_compute_rfq_line_ids', string='Quotation Lines', store=True)
    store_request_id = fields.Many2one(
        'store.request', string='Store Request')
    store_requested_by = fields.Many2one('hr.employee',
                                         string='Store Requested By',
                                         related='store_request_id.requested_by',
                                         tracking=True)
    product_category_id = fields.Many2one(
        'product.category', string="Product Category", required=True)
    purpose = fields.Text(string='Purpose')
    total_amount = fields.Monetary(
        string='Total Amount', compute='_compute_total_amount', store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    company_id = fields.Many2one(
        'res.company', string='Company', tracking=True, default=lambda self: self.env.company.id)
    department_id = fields.Many2one(
        'hr.department', string='Department', tracking=True, compute='_compute_department_id')
    committee_member_ids = fields.One2many(
        'committee.member', 'rfp_id', string='Committee Members')
    can_current_user_approve = fields.Boolean(
        string='Can Current User Approve',
        compute='_compute_can_current_user_approve',
        store=False
    )
    has_rejected_member = fields.Boolean(
        string='Has Rejected Member',
        compute='_compute_has_rejected_member',
        store=False
    )
    current_user_member_id = fields.Many2one(
        'committee.member',
        string='Current User Committee Member',
        compute='_compute_can_current_user_approve',
        store=False
    )
    net_pay = fields.Monetary(
        string='Net Pay',
        compute='_compute_net_pay',
        store=False,
        help="Net Pay amount calculated from winning bids (Total + VAT - Withholding)."
    )
    requires_ceo_approval = fields.Boolean(
        string='Requires CEO Approval',
        compute='_compute_requires_ceo_approval',
        store=False,
        help="Indicates if this purchase request requires CEO approval based on the configured threshold."
    )

    requested_date = fields.Datetime(
        string='Requested Date', required=True, default=fields.Datetime.now, tracking=True)
    required_date = fields.Date(string='Required Date', tracking=True,
                                default=lambda self: fields.Date.add(fields.Date.today(), days=5))
    date_approve = fields.Date(string='Reviewed On')
    date_ordered = fields.Date(string='Ordered On')
    internal_notes = fields.Text(string="Internal Notes")
    decision = fields.Text(string="Decision")

    submitted_by = fields.Many2one(
        'res.users', string='Submitted By')
    verified_by = fields.Many2one('res.users', string="Verified By")
    approved_by = fields.Many2one(
        'res.users', string='Approved By')
    f_approved_by = fields.Many2one(
        'res.users', string='Final Approved By')
    f_approved_date = fields.Date(string='Final Approved On')

    source_rfp_id = fields.Many2one(
        'supplies.rfp', string='Source RFP')

    merged_from_references = fields.Text(
        string="Merged From",
        help="Contains the RFP Numbers of the requests that were merged to create this record."
    )
    direct_purchase_id = fields.Many2one(
        'purchase.order', string="Direct Purchase Order")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('rfp_number', 'New') == 'New':
                # if vals.get('purchase_origin') == 'local':
                prefix = 'PR'
                sequence_code = 'purchase.request.local'
                sequence_number = self.env['ir.sequence'].next_by_code(
                    sequence_code)
                vals['rfp_number'] = f"{prefix.upper()}-{sequence_number}"
        return super(SuppliesRfp, self).create(vals_list)

        @api.onchange('store_request_id')
        def _onchange_store_request_id(self):
            if self.store_request_id:
                self.department_id = self.store_request_id.department_id
                self.company_id = self.store_request_id.company_id
                self.purpose = self.store_request_id.purpose

    @api.depends('store_request_id.requested_by.department_id')
    def _compute_department_id(self):
        for rec in self:
            rec.department_id = rec.store_request_id.requested_by.department_id if rec.store_request_id else False

    @api.depends('rfq_ids.order_line')
    def _compute_rfq_line_ids(self):
        for rfp in self:
            rfp.rfq_line_ids = rfp.rfq_ids.mapped('order_line')

    @api.depends('rfq_ids')
    def _compute_rfq_count(self):
        for rec in self:
            rec.rfq_count = len(rec.rfq_ids)

    @api.depends('total_amount')
    def _compute_total_amount(self):
        """Compute total amount from RFQ lines"""
        for rec in self:
            # Calculate from winning prices (lowest price for each product)
            total = 0.0
            valid_rfq_lines = rec.rfq_line_ids.filtered(
                lambda l: l.order_id.final_po == False
            )
            for product_line in rec.product_line_ids:
                prod = product_line.product_id
                all_lines_for_product = valid_rfq_lines.filtered(
                    lambda l: l.product_id == prod and not l.out_of_stock and l.price_subtotal > 0
                )
                if all_lines_for_product:
                    winning_line = min(all_lines_for_product,
                                       key=lambda l: l.price_subtotal)
                    total += winning_line.price_subtotal
            rec.total_amount = total

    @api.depends('rfq_line_ids', 'product_line_ids')
    def _compute_net_pay(self):
        """Compute Net Pay from winning bids (Total + VAT - Withholding)"""
        for rec in self:
            rec.net_pay = 0.0
            valid_rfq_lines = rec.rfq_line_ids.filtered(
                lambda l: l.order_id.final_po == False
            )

            if not valid_rfq_lines:
                continue

            # Calculate based on winning suppliers (lowest prices)
            winning_lines_by_supplier = self.env['purchase.order.line']
            for product_line in rec.product_line_ids:
                prod = product_line.product_id
                all_lines_for_product = valid_rfq_lines.filtered(
                    lambda l: l.product_id == prod and not l.out_of_stock and l.price_subtotal > 0
                )
                if all_lines_for_product:
                    winning_line = min(all_lines_for_product,
                                       key=lambda l: l.price_subtotal)
                    winning_lines_by_supplier |= winning_line

            if not winning_lines_by_supplier:
                continue

            # Calculate combined totals
            combined_total = sum(
                winning_lines_by_supplier.mapped('price_subtotal'))
            combined_tax = sum(winning_lines_by_supplier.mapped('price_tax'))
            combined_withholding = 0.0

            # Get unique suppliers from winning lines
            winning_suppliers = winning_lines_by_supplier.mapped(
                'order_id.partner_id')

            # Calculate withholding from all suppliers
            for supplier in winning_suppliers:
                supplier_winning_lines = winning_lines_by_supplier.filtered(
                    lambda l: l.order_id.partner_id == supplier
                )
                supplier_rfq = supplier_winning_lines[0].order_id if supplier_winning_lines else False

                if supplier_rfq and supplier_rfq.tax_totals:
                    subtotals = supplier_rfq.tax_totals.get('subtotals', [])
                    for subtotal_item in subtotals:
                        tax_groups = subtotal_item.get('tax_groups', [])
                        for tax_group in tax_groups:
                            group_name = (tax_group.get(
                                'group_name', '') or '').lower()
                            group_label = (tax_group.get(
                                'group_label', '') or '').lower()
                            if 'withhold' in group_name or 'withholding' in group_name or 'withhold' in group_label or 'withholding' in group_label:
                                combined_withholding += abs(
                                    tax_group.get('tax_amount_currency', 0))

            # Calculate Net Pay
            rec.net_pay = (combined_total + combined_tax) - \
                combined_withholding

    @api.depends('net_pay')
    def _compute_requires_ceo_approval(self):
        """Compute if CEO approval is required based on threshold using Net Pay"""
        for rec in self:
            rec.requires_ceo_approval = False
            if rec.net_pay > 0:
                threshold = float(self.env['ir.config_parameter'].sudo().get_param(
                    'vendor_bid.ceo_approval_threshold', '0.0'
                ))
                if threshold > 0 and rec.net_pay >= threshold:
                    rec.requires_ceo_approval = True

    @api.model
    def _get_rfq_domain(self):
        domain = []
        for rec in self:
            domain = [('rfp_id', '=', rec.id), ('final_po', '=', False)]
        return domain

    def action_submit(self):
        if not self.product_line_ids:
            raise UserError('Please add product lines before submitting.')

        if not all(self.product_line_ids.mapped('product_qty')):
            raise UserError('Product quantity must be greater than 0')

        self.write({'state': 'submitted', 'submitted_by': self.env.user.id})

    def action_approve(self):
        self.write({'state': 'approved', 'date_approve': fields.Date.today(
        ), 'approved_by': self.env.user.id})

    def action_final_approve(self):
        """Final approval after committee approval"""
        self.write({
            'state': 'f_approved',
            'f_approved_date': fields.Date.today(),
            'f_approved_by': self.env.user.id
        })

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_close(self):
        self.write({'state': 'evaluation'})

    def action_accept(self):
        self.write({'state': 'accepted'})

    def action_initial_verfied(self):
        self.write({'state': 'initial_verfayed',
                   'verified_by': self.env.user.id})

    def action_Verfay(self):
        self.write({'state': 'verfayed'})

    def action_open_split_wizard(self):
        """Open the split RFP wizard"""
        self.ensure_one()
        if not self.product_line_ids:
            raise UserError(_('No product lines to split.'))

        return {
            'name': _('Split RFP'),
            'type': 'ir.actions.act_window',
            'res_model': 'rfp.split.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id, 'default_rfp_id': self.id},
        }

    def action_return(self):
        for record in self:
            if record.state == 'approved':
                record.write({'state': 'committee_approved'})
            elif record.state == 'committee_approved':
                record.write({'state': 'committee_approving'})
            elif record.state == 'committee_approving':
                record.write({'state': 'accepted'})
            elif record.state == 'evaluation':
                record.write({'state': 'approved'})
            elif record.state == 'accepted':
                record.write({'state': 'evaluation'})

    def action_view_quotations(self):
        self.ensure_one()
        return {
            'name': 'Quotations',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('rfp_id', '=', self.id), ('final_po', '=', False)],
            'type': 'ir.actions.act_window',
        }

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'name': 'Orders',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('rfp_id', '=', self.id), ('final_po', '=', True), ('state', '=', 'purchase')],
            'type': 'ir.actions.act_window',
        }

    @api.onchange('purchase_origin')
    def _onchange_purchase_origin(self):

        if not self.purchase_origin:
            return
        group_map = {
            'local': 'VendorBid.group_local_purchase_committee_member',
            'foreign': 'VendorBid.group_foreign_purchase_committee_member',
        }
        xml_id = group_map.get(self.purchase_origin)
        group = self.env.ref(xml_id)

        if not group:
            self.committee_member_ids = [Command.clear()]
            return

        employees = self.env['hr.employee'].search([
            ('user_id', 'in', group.users.ids)
        ])
        new_members_list = [Command.clear()]

        for employee in employees:
            new_members_list.append(
                Command.create({
                    'member_id': employee.id,
                    'role': 'member',
                    'approval_status': 'pending',
                })
            )
            self.committee_member_ids = new_members_list

    @api.depends('committee_member_ids.approval_status', 'committee_member_ids.related_user_id', 'state')
    def _compute_can_current_user_approve(self):
        """Check if current user can approve based on their committee member line"""
        current_user = self.env.user
        for rfp in self:
            rfp.can_current_user_approve = False
            rfp.current_user_member_id = False
            if rfp.state in ('accepted', 'committee_approving'):
                user_member = rfp.committee_member_ids.filtered(
                    lambda m: m.related_user_id == current_user and m.approval_status == 'pending'
                )
                if user_member:
                    rfp.can_current_user_approve = True
                    rfp.current_user_member_id = user_member[0]

    def action_committee_approve_current_user(self):
        """Approve action for current user from header button"""
        self.ensure_one()
        if not self.can_current_user_approve or not self.current_user_member_id:
            raise UserError(
                _("You cannot approve this RFP. Please check if you are a committee member with pending approval."))
        self.current_user_member_id.action_committee_approve()

    # def action_committee_reject_current_user(self):
    #     """Reject action for current user from header button"""
    #     self.ensure_one()
    #     if not self.can_current_user_approve or not self.current_user_member_id:
    #         raise UserError(
    #             _("You cannot reject this RFP. Please check if you are a committee member with pending approval."))
    #     self.current_user_member_id.action_committee_reject()

    def action_committee_reject_current_user(self):
        """Reject action for current user from header button"""
        self.ensure_one()
        if not self.can_current_user_approve or not self.current_user_member_id:
            raise UserError(
                _("You cannot reject this RFP. Please check if you are a committee member with pending approval."))

        return {
            'name': _('Reject RFP'),
            'type': 'ir.actions.act_window',
            'res_model': 'committee.member.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_committee_member_id': self.current_user_member_id.id,
            }
        }

    def _check_all_committee_approved(self):
        """Check if all committee members have approved"""
        if not self.committee_member_ids:
            return False
        return all(member.approval_status == 'approved' for member in self.committee_member_ids)

    def _check_at_least_one_approved(self):
        """Check if at least one committee member has approved"""
        if not self.committee_member_ids:
            return False
        return any(member.approval_status == 'approved' for member in self.committee_member_ids)

    def _check_has_rejected_member(self):
        """Check if at least one committee member has rejected status"""
        if not self.committee_member_ids:
            return False
        return any(member.approval_status == 'rejected' for member in self.committee_member_ids)

    @api.depends('committee_member_ids.approval_status')
    def _compute_has_rejected_member(self):
        """Compute if at least one committee member has rejected status"""
        for rfp in self:
            rfp.has_rejected_member = rfp._check_has_rejected_member()

    def action_re_request_approval(self):
        """Reset rejected committee members back to pending status"""
        self.ensure_one()
        if not self.has_rejected_member:
            raise UserError(
                _('No rejected committee members found. Cannot re-request approval.'))

        # Reset all rejected members back to pending
        rejected_members = self.committee_member_ids.filtered(
            lambda m: m.approval_status == 'rejected')
        rejected_members.write({
            'approval_status': 'pending',
            'approval_date': False
        })

        # Reset state if needed
        if self.state in ('committee_approved', 'approved'):
            # Move back to committee_approving state to allow re-approval
            self.write({'state': 'committee_approving'})

        return True

    def _check_and_move_to_committee_approving_or_approved(self):
        """Check committee approval status and move state accordingly"""
        for rfp in self:
            if rfp.state == 'accepted':
                # Move to committee_approving when at least one member approves
                if rfp._check_at_least_one_approved():
                    rfp.write({'state': 'committee_approving'})
            elif rfp.state == 'committee_approving':
                # Move to committee_approved when all members approve
                if rfp._check_all_committee_approved():
                    rfp.write({'state': 'committee_approved'})

    def action_merge(self):
        if len(self) < 2:
            raise UserError(
                _("Please select at least two Purchase Requests to merge."))

        template_rfp = self[0]

        allowed_states = ['approved']

        source_refs = []

        for rfp in self:
            if rfp.company_id != template_rfp.company_id:
                raise UserError(_(
                    "Cannot merge requests from different Companies.\n"
                    "Check RFP: %s", rfp.rfp_number
                ))

            if rfp.purchase_origin != template_rfp.purchase_origin:
                raise UserError(_(
                    "Cannot merge requests with different Purchase Origins.\n"
                    "Check RFP: %s", rfp.rfp_number
                ))

            # if rfp.state not in allowed_states:
            #     raise UserError(_(
            #         "Requests can only be merged before the 'Evaluation' stage.\n"
            #         "RFP %s is currently in state '%s'.", rfp.rfp_number, rfp.state
            #     ))

            if rfp.rfq_count > 0:
                raise UserError(_(
                    "Cannot merge requests that already have Quotations attached.\n"
                    "RFP %s has %s RFQs.", rfp.rfp_number, rfp.rfq_count
                ))

            source_refs.append(rfp.rfp_number)

            grouped_lines = {}

        for rfp in self:
            for line in rfp.product_line_ids:
                prod_id = line.product_id.id
                if prod_id in grouped_lines:
                    grouped_lines[prod_id]['product_qty'] += line.product_qty

                    if line.product_name and line.description not in grouped_lines[prod_id]['description']:
                        grouped_lines[prod_id]['description'] += f"\n{line.product_name}"
                else:
                    grouped_lines[prod_id] = {
                        'product_id': prod_id,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        'product_name': line.product_name,
                        'description': line.description,
                    }

        line_commands = [Command.create(vals)
                         for vals in grouped_lines.values()]

        new_rfp_vals = {
            'company_id': template_rfp.company_id.id,
            'department_id': template_rfp.department_id.id,
            'purchase_origin': template_rfp.purchase_origin,
            'purchase_type': template_rfp.purchase_type,
            'product_category_id': template_rfp.product_category_id.id,
            'currency_id': template_rfp.currency_id.id,
            'purpose': _("Merged from: %s") % ", ".join(source_refs),
            'requested_date': fields.Datetime.now(),
            'state': 'approved',
            'product_line_ids': line_commands,
            'merged_from_references': ", ".join(source_refs),
            'submitted_by': self.env.user.id,
        }

        new_rfp = self.create(new_rfp_vals)

        for rfp in self:
            rfp.message_post(
                body=_(
                    "This request was included in a merge operation. "
                    "New Request created: <a href=# data-oe-model=supplies.rfp data-oe-id=%d>%s</a>"
                ) % (new_rfp.id, new_rfp.rfp_number)
            )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'supplies.rfp',
            'view_mode': 'form',
            'res_id': new_rfp.id,
            'target': 'current',
        }
