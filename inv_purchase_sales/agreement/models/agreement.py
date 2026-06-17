# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Agreement(models.Model):
    _name = "sale.agreement"
    _description = "Agreement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "code"

    code = fields.Char(
        required=True,
        string="Contract Agreement No.",
        tracking=True,
        copy=False,
    )
    name = fields.Char(required=True, string="Name", copy=False)

    partner_id = fields.Many2one(
        "res.partner",
        string="Buyer",
        ondelete="restrict",
        domain=[("parent_id", "=", False)],
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    description = fields.Text(string="Description")

    agreement_type_id = fields.Many2one(
        "agreement.type",
        string="Agreement Type",
        help="Select the type of agreement",
    )

    active = fields.Boolean(default=True)
    signature_date = fields.Date(tracking=True, default=lambda self: fields.Date.today())
    start_date = fields.Date(
        string="Agreement Date",
        tracking=True,
        required=True,
    )
    end_date = fields.Date(
        string="Agreement End Date",
        tracking=True,
        required=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        compute="_compute_currency_id",
        store=True,
        tracking=True,
    )
    payment_type = fields.Selection(
        [
            ("lc", "LC"),
            ("tt", "TT"),
            ("cad", "CAD"),
        ],
        string="Payment Type",
        required=True,
        default="lc",
        tracking=True,
    )
    partial_shipment = fields.Boolean(string="Partial Shipment", tracking=True)
    country_of_delivery_id = fields.Many2one(
        "res.country",
        string="Country of Delivery",
        default=lambda self: self.env.company.country_id,
        tracking=True,
    )
    port_of_loading = fields.Char(string="Port of Loading", tracking=True)
    port_of_discharge = fields.Char(string="Port of Discharge", tracking=True)
    product_categ_id = fields.Many2one(
        "product.category",
        string="Product Category",
        tracking=True,
    )
    source = fields.Selection(
        [
            ("local", "Local"),
            ("import", "Import"),
            ("export", "Export"),
        ],
        string="Source",
        default="import",
        tracking=True,
    )
    incoterm_id = fields.Many2one(
        "account.incoterms",
        string="Incoterm",
        tracking=True,
    )
    freight_included = fields.Boolean(string="Freight Included", tracking=True)
    exporter_bank_id = fields.Many2one(
        "res.partner",
        string="Exporter Bank",
        domain=[("is_company", "=", True)],
        tracking=True,
    )
    packaging_description = fields.Text(string="Packaging Description", tracking=True)

    # --- MODIFIED STATE SELECTION ---
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("review", "Review"),
            ("approved", "Approved"),
            ("refuse", "Refused"),
            ("done", "Done"), # Keeping Done for final closure if needed
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    expiration_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("running", "Running"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
            ("closed", "Closed"),
        ],
        string="Expiration Status",
        compute="_compute_expiration_status",
        store=True,
        tracking=True,
    )
    sale_order_ids = fields.One2many(
        "sale.order",
        "agreement_id",
        string="Sale Orders",
        readonly=True,
        tracking=True,
    )
    sale_count = fields.Integer(string="Sale Order", compute="_count_sale_order")
    line_ids = fields.One2many(
        "agreement.line",
        "agreement_id",
        string="Agreement Lines",
        copy=True,
    )
    attachment = fields.Binary(
        string="Attachment"
    )
    attachment_name = fields.Char(string="Attachment Name")

    total_value = fields.Monetary(
        string="Total Value",
        compute="_compute_amounts",
        store=True,
        readonly=True,
        currency_field="currency_id",
    )
    amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    amount_tax = fields.Monetary(
        string="Taxes",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    amount_total = fields.Monetary(
        string="Total",
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    tax_totals = fields.Binary(compute="_compute_tax_totals", exportable=False)
    agreement_category = fields.Selection(
        [
            ("product_sale", "Product Sale"),
            ("maintenance", "Maintenance"),
        ],
        string="Agreement Category",
        required=True,
        default="product_sale",
        tracking=True,
    )
    allowed_product_ids = fields.Many2many(
        'product.product',
        string='Allowed Products',
        compute='_compute_allowed_products',
        store=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault("name", vals.get("code") or _("New Agreement"))
        return super().create(vals_list)

    @api.onchange("code")
    def _onchange_code_set_name(self):
        if self.code:
            self.name = self.code

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for rec in self:
            rec.purchase_order_count = len(rec.purchase_order_ids)

    @api.depends("line_ids.currency_id")
    def _compute_currency_id(self):
        for agreement in self:
            agreement.currency_id = (
                agreement.line_ids[:1].currency_id
                or agreement.env.company.currency_id
            )

    @api.onchange('agreement_category')
    def _compute_allowed_products(self):
        Product = self.env['product.product']
        for rec in self:
            if rec.agreement_category == 'maintenance':
                rec.allowed_product_ids = Product.search([('type', '=', 'service')])
            else:
                rec.allowed_product_ids = Product.search([('type', '!=', 'service')])

    @api.onchange('product_categ_id')
    def _onchange_product_categ_id(self):
        if not self.product_categ_id or not self.line_ids:
            return
        allowed_categ_ids = self.env['product.category'].search([
            ('id', 'child_of', self.product_categ_id.id),
        ]).ids
        for line in self.line_ids:
            if line.product_id and line.product_id.categ_id.id not in allowed_categ_ids:
                line.product_id = False

    def _count_sale_order(self):
        for record in self:
            record.sale_count = len(self.env['sale.order'].search([('agreement_id', '=', self.id)]))

    @api.depends(
        "line_ids.quantity",
        "line_ids.unit_price",
        "line_ids.tax_ids",
        "line_ids.currency_id",
        "currency_id",
        "company_id",
    )
    def _compute_amounts(self):
        AccountTax = self.env["account.tax"]
        for agreement in self:
            base_lines = [
                line._prepare_base_line_for_taxes_computation()
                for line in agreement.line_ids
            ]
            AccountTax._add_tax_details_in_base_lines(base_lines, agreement.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, agreement.company_id)
            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=agreement.currency_id or agreement.company_id.currency_id,
                company=agreement.company_id,
            )
            agreement.amount_untaxed = tax_totals["base_amount_currency"]
            agreement.amount_tax = tax_totals["tax_amount_currency"]
            agreement.amount_total = tax_totals["total_amount_currency"]
            agreement.total_value = agreement.amount_total

    @api.depends_context("lang")
    @api.depends(
        "line_ids.quantity",
        "line_ids.unit_price",
        "line_ids.tax_ids",
        "line_ids.currency_id",
        "currency_id",
        "company_id",
    )
    def _compute_tax_totals(self):
        AccountTax = self.env["account.tax"]
        for agreement in self:
            base_lines = [
                line._prepare_base_line_for_taxes_computation()
                for line in agreement.line_ids
            ]
            AccountTax._add_tax_details_in_base_lines(base_lines, agreement.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, agreement.company_id)
            agreement.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=agreement.currency_id or agreement.company_id.currency_id,
                company=agreement.company_id,
            )

    @api.depends("start_date", "end_date", "state")
    def _compute_expiration_status(self):
        today = fields.Date.today()
        for rec in self:
            if rec.state == "draft":
                rec.expiration_status = "draft"
            elif rec.state == "done":
                rec.expiration_status = "closed"
            elif rec.state == "refuse":
                rec.expiration_status = "cancelled"
            # MODIFIED: Treat 'approved' as the running state (previously confirmed)
            elif rec.state == "approved":
                if not rec.start_date or not rec.end_date:
                    rec.expiration_status = "running"
                elif rec.start_date > today:
                    rec.expiration_status = "draft"
                elif rec.end_date < today:
                    rec.expiration_status = "expired"
                else:
                    rec.expiration_status = "running"
            else:
                # Fallback for submitted/review
                rec.expiration_status = "draft"

    def _check_expiration(self):
        for record in self:
            agreements = self.env['sale.agreement'].search([
                ('expiration_status', 'not in', ['expired', 'cancelled', 'closed'])
            ])
            for agreement in agreements:
                agreement._compute_expiration_status()

    def copy(self, default=None):
        """Always assign a value for code because is required"""
        default = dict(default or {})
        if default.get("code", False):
            return super().copy(default)
        default.setdefault("code", self.env._("%(code)s (copy)", code=self.code))
        return super().copy(default)

    # --- NEW WORKFLOW ACTIONS ---

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                 raise ValidationError(_("Only draft agreements can be submitted."))
            rec.state = 'submitted'

    def action_review(self):
        for rec in self:
            if rec.state != 'submitted':
                 raise ValidationError(_("Agreement must be Submitted before Review."))
            rec.state = 'review'

    def action_approve(self):
        for rec in self:
            if rec.state != 'review':
                 raise ValidationError(_("Agreement must be in Review before Approval."))
            rec.state = 'approved'

    def action_refuse(self):
        for rec in self:
            if rec.state not in ['submitted', 'review']:
                 raise ValidationError(_("Only submitted or under-review agreements can be refused."))
            rec.state = 'refuse'

    def action_draft(self):
        """Reset to draft"""
        for rec in self:
            rec.state = 'draft'

    def action_done(self):
        """Mark as Done (Closed)"""
        for rec in self:
            if rec.state == "approved":
                rec.state = "done"
            else:
                raise ValidationError(_("Only approved agreements can be done."))

    def view_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('agreement_id', '=', self.id)],
        }

    def _get_sale_order_state_selection(self):
        selection = self.env["sale.order"]._fields["state"].selection
        if callable(selection):
            selection = selection(self.env["sale.order"])
        return {value for value, _label in selection}

    def _prepare_sale_order_vals(self):
        self.ensure_one()
        valid_states = self._get_sale_order_state_selection()
        vals = {
            "partner_id": self.partner_id.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "origin": self.code,
            "date_order": fields.Date.today(),
            "agreement_id": self.id,
        }
        sale_order_fields = self.env["sale.order"]._fields
        if "order_submit" in valid_states:
            vals["state"] = "order_submit"
            if "order_type" in sale_order_fields:
                vals["order_type"] = "order"
        else:
            vals["state"] = "draft"
        if "contract_ref" in sale_order_fields:
            vals["contract_ref"] = self.code
        if "sale_category" in sale_order_fields and self.agreement_category:
            vals["sale_category"] = self.agreement_category
        return vals

    def action_create_sale_order(self):
        """Create a sale order from the agreement with selected lines"""
        self.ensure_one()
        # MODIFIED: Check for approved instead of confirmed
        if self.state != "approved":
            raise ValidationError(_("Only approved agreements can create sale orders."))
        if not self.line_ids:
            raise ValidationError(_("No agreement lines defined. Please add at least one line."))

        # If no line_ids provided, use all lines with remaining quantity
        lines_to_process = self.line_ids.filtered(lambda l: l.quantity > l.ordered_qty)
        if not lines_to_process:
            raise ValidationError(_("No remaining quantity to order on agreement lines."))

        # Create sale order
        sale_order = self.env["sale.order"].create(self._prepare_sale_order_vals())

        # Create sale order lines from selected agreement lines
        for line in lines_to_process:
            remaining_qty = line.quantity - line.ordered_qty
            if remaining_qty <= 0:
                continue
            self.env["sale.order.line"].create({
                "order_id": sale_order.id,
                "product_id": line.product_id.id,
                "name": line.description or line.product_id.name,
                "product_uom_qty": remaining_qty,
                "product_uom": line.uom_id.id,
                "price_unit": line.unit_price,
                "tax_id": [(6, 0, line.tax_ids.ids)],
            })

        self.sale_order_ids = [(4, sale_order.id)]
        # Update ordered_qty after sale order creation
        self.line_ids._compute_ordered_qty()
        
        # Optional: Auto-close if fully ordered? 
        # Keeping existing logic but mapping to done
        if all(line.quantity <= line.ordered_qty for line in self.line_ids):
            self.state = "done"
            
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": sale_order.id,
            "view_mode": "form",
            "target": "current",
        }

class AgreementLine(models.Model):
    _name = "agreement.line"
    _description = "Agreement Lines"

    agreement_id = fields.Many2one(
        "sale.agreement",
        string="Agreement",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
    )
    description = fields.Text(string="Description")
    uom_id = fields.Many2one(
        "uom.uom",
        string="Measurement Unit",
        required=True,
        related="product_id.uom_id",
    )
    quantity = fields.Float(string="Quantity", required=True, default=1.0)
    ordered_qty = fields.Float(
        string="Delivered",
        compute="_compute_ordered_qty",
        store=True,
        readonly=True,
    )
    unit_price = fields.Float(string="Unit Price", required=True, default=0.0)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    total_price = fields.Float(
        string="Total Price",
        compute="_compute_total_price",
        store=True,
    )
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        domain=[("type_tax_use", "=", "sale")],
    )

    @api.depends("agreement_id.sale_order_ids.order_line", "agreement_id.sale_order_ids.order_line.qty_delivered")
    def _compute_ordered_qty(self):
        for line in self:
            # Sum quantities from sale order lines for this product
            total_ordered = sum(
                sol.qty_delivered
                for so in line.agreement_id.sale_order_ids
                for sol in so.order_line
                if sol.product_id == line.product_id and sol.order_id.state != "cancel"
            )
            line.ordered_qty = total_ordered

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if "currency_id" not in defaults:
            agreement_id = self.env.context.get("default_agreement_id")
            if agreement_id:
                agreement = self.env["sale.agreement"].browse(agreement_id)
                if agreement.line_ids:
                    defaults["currency_id"] = agreement.line_ids[0].currency_id.id
                elif agreement.currency_id:
                    defaults["currency_id"] = agreement.currency_id.id
        return defaults

    @api.depends("quantity", "unit_price", "tax_ids", "currency_id")
    def _compute_total_price(self):
        for line in self:
            if not line.agreement_id:
                line.total_price = line.unit_price * line.quantity
                continue
            base_line = line._prepare_base_line_for_taxes_computation()
            self.env["account.tax"]._add_tax_details_in_base_line(
                base_line, line.agreement_id.company_id
            )
            line.total_price = base_line["tax_details"]["raw_total_included_currency"]

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        self.ensure_one()
        return self.env["account.tax"]._prepare_base_line_for_taxes_computation(
            self,
            **{
                "tax_ids": self.tax_ids,
                "quantity": self.quantity,
                "price_unit": self.unit_price,
                "partner_id": self.agreement_id.partner_id,
                "currency_id": self.currency_id,
                **kwargs,
            },
        )

    def init(self):
        super().init()
        self.env.cr.execute("""
            UPDATE agreement_line AS al
               SET currency_id = sa.currency_id
              FROM sale_agreement AS sa
             WHERE al.agreement_id = sa.id
               AND al.currency_id IS NULL
               AND sa.currency_id IS NOT NULL
        """)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            if self.agreement_id.product_categ_id:
                allowed_categ_ids = self.env['product.category'].search([
                    ('id', 'child_of', self.agreement_id.product_categ_id.id),
                ]).ids
                if self.product_id.categ_id.id not in allowed_categ_ids:
                    self.product_id = False
                    return
            elif self.agreement_id:
                self.agreement_id.product_categ_id = self.product_id.categ_id
            self.uom_id = self.product_id.uom_id
            self.unit_price = self.product_id.lst_price
            self.description = self.product_id.name
            self.tax_ids = self.product_id.taxes_id