# © 2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class Agreement(models.Model):
    _name = "sale.agreement"
    _description = "Agreement"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    code = fields.Char(required=False, string="Code", tracking=True)
    name = fields.Char(required=True, string="Name")
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
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
    start_date = fields.Date(tracking=True, required=True)
    end_date = fields.Date(tracking=True, required=True)

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

    agreement_category = fields.Selection([
        ('product_sale', 'New Product'),
        ('maintenance', 'Maintenance'),
        ('test', 'Test')
    ])

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

    total_value = fields.Float(
        string="Total Value",
        compute="_compute_total_value",
        store=True,
        readonly=True,
    )
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

    @api.onchange('agreement_category')
    def _compute_allowed_products(self):
        Product = self.env['product.product']
        for rec in self:
            if rec.agreement_category == 'maintenance':
                rec.allowed_product_ids = Product.search([('type', '=', 'service')])
            else:
                rec.allowed_product_ids = Product.search([('type', '!=', 'service')])

    def _count_sale_order(self):
        for record in self:
            record.sale_count = len(self.env['sale.order'].search([('agreement_id', '=', self.id)]))

    @api.depends("line_ids.total_price")
    def _compute_total_value(self):
        for rec in self:
            rec.total_value = sum(line.total_price for line in rec.line_ids)

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

        # Create sale order
        sale_order = self.env["sale.order"].create({
            "partner_id": self.partner_id.id,
            "company_id": self.company_id.id,
            "origin": self.code,
            "date_order": fields.Date.today(),
            "agreement_id": self.id,
            "state": "order_submit",
        })

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
        string="Unit of Measure",
        required=True,
        related="product_id.uom_id"
    )
    quantity = fields.Float(string="Quantity", required=True, default=1.0)
    ordered_qty = fields.Float(
        string="Delivered",
        compute="_compute_ordered_qty",
        store=True,
        readonly=True,
    )
    unit_price = fields.Float(string="Unit Price", required=True, default=0.0)
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

    @api.depends("quantity", "unit_price", "tax_ids")
    def _compute_total_price(self):
        for line in self:
            # Include taxes in total price calculation
            taxes = line.tax_ids.compute_all(
                line.unit_price,
                quantity=line.quantity,
                product=line.product_id,
                partner=line.agreement_id.partner_id,
            )
            line.total_price = taxes["total_included"]

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.unit_price = self.product_id.lst_price
            self.description = self.product_id.name
            self.tax_ids = self.product_id.taxes_id