from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class ProductWarranty(models.Model):
    _name = 'product.warranty'
    _description = 'Product Warranty'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Warranty Ref', required=True, copy=False,readonly=False, 
                       default=lambda self: _('New'), tracking=True)
    
    partner_id = fields.Many2one('res.partner', string='Customer (TO)', required=True, tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', tracking=True)
    
    # Product Details
    product_id = fields.Many2one('product.product', string='Product Name', required=True, tracking=True)
    product_rating = fields.Char(string='Rating', help="e.g. S-M-100/15KVA", tracking=True)
    serial_number = fields.Char(string='Serial Number', required=True, tracking=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                 default=lambda self: self.env.company)

    
    # Dates
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today, required=True, tracking=True)
    warranty_months = fields.Integer(string='Duration (Months)', default=12, required=True)
    end_date = fields.Date(string='Expiration Date', compute='_compute_end_date', store=True)
    
    # Approval Details
    approval_date = fields.Date(string='Dated', readonly=True, copy=False)
    approver_id = fields.Many2one('res.users', string='Approver', readonly=True, copy=False)
    
    # Default Legal Text (Editable per record)
    default_text = """WHEREAS WE WAGWAGO TRADING PLC WHO ARE ESTABLISHED AND REPUTABLE IMPORTER OF DISTRIBUTION TRANSFORMER AND ITS ACCESSORIES FOR ANY GOVERNMENTAL AND PRIVAT SECTORS, DO HEREBY WARRANT THAT:

A) THE GOODS TO BE SUPPLIED UNDER THE CONTRACT ARE NEW, UNUSED, OF THE MOST RECENT OR CURRENT SPECIFICATION AND INCORPORATE ALL RECENT IMPROVEMENTS IN DESIGN AND MATERIALS.

B) THE TRANSFORMER ARE ACCORDING TO IEC TECHNICAL SPECIFICATIONS.

THE WARRANTY WILL REMAIN VALID ONE YEAR WARRANTY FROM DATE OF COMMISSIONING OR 12 MONTHS FROM DATE OF DELIVERY, WHICHEVER IS EARLIER."""
    
    certificate_body = fields.Text(string="Certificate Content", default=default_text)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('review', 'Review'),
        ('running', 'Running'),
        ('expired', 'Expired'),
        ('void', 'Voided'),
    ], string='Status', default='draft', tracking=True, compute='_compute_state', store=True, readonly=False)

    # --- SEQUENCING ---
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('product.warranty') or _('New')
        return super(ProductWarranty, self).create(vals_list)

    # --- COMPUTE METHODS ---
    @api.depends('start_date', 'warranty_months')
    def _compute_end_date(self):
        for record in self:
            if record.start_date and record.warranty_months:
                record.end_date = record.start_date + relativedelta(months=record.warranty_months)

    @api.depends('end_date')
    def _compute_state(self):
        today = fields.Date.today()
        for record in self:
            if record.state in ['draft', 'submitted', 'review', 'void']:
                continue
            if record.end_date and record.end_date < today:
                record.state = 'expired'
            else:
                record.state = 'running'

    # --- ACTIONS ---
    def action_submit(self):
        self.state = 'submitted'

    def action_review(self):
        self.state = 'review'

    def action_approve(self):
        """ Capture Approver and Date on Approval """
        self.state = 'running'
        self.approval_date = fields.Date.today()
        self.approver_id = self.env.user
        self._compute_state()

    def action_void(self):
        self.state = 'void'

    def action_draft(self):
        self.state = 'draft'

    def action_print_warranty(self):
        self.ensure_one()
        if self.state not in ['running', 'expired']:
            raise ValidationError(_("You can only print the warranty certificate after it has been Approved."))
            
        return self.env.ref('custom_sale_agreement.action_report_product_warranty').report_action(self)
    def action_send_email(self):
        """ Generates an editable email with the full template content """
        self.ensure_one()
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        
        # Prepare Approver Info (Default to current user if not yet approved)
        approver = self.approver_id or self.env.user
        app_name = approver.name.upper()
        app_job = approver.function.upper() if approver.function else "MANAGER"
        app_company = self.env.company.name.upper()
        date_str = self.approval_date or fields.Date.today()

        # Construct Email Body
        body = f"""
        <p><strong>TO:</strong> {self.partner_id.name}</p>
        <p><strong>NAME:</strong> {self.product_id.name}</p>
        <p><strong>RATING:</strong> {self.product_rating or 'N/A'}</p>
        <p><strong>SERIAL NO:</strong> {self.serial_number}</p>
        <br/>
        <p>{self.certificate_body.replace(chr(10), '<br/>')}</p>
        <br/>
        <p><strong>DATED THIS:</strong> {date_str}</p>
        <br/><br/>
        <p>{app_name}<br/>{app_job}<br/>{app_company}</p>
        """

        ctx = dict(
            default_model='product.warranty',
            default_res_ids=[self.id],
            default_body=body,
            default_subject=f"Warranty Certificate - {self.name}",
            default_composition_mode='comment',
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }