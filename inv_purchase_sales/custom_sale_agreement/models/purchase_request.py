# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Ref No', required=True, copy=False, readonly=False, 
                       default=lambda self: _('New'))
    # 1. Add the Company Field
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        required=True, 
        default=lambda self: self.env.company
    )

    payment_request_id = fields.Many2one('payment.request', string="Source Payment Request", readonly=True)

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    
    #  Department & Address
    department_name = fields.Char(string='To', default="Department")
    address_amharic = fields.Char(string='Address ')
    
    date = fields.Date(string='Date', default=fields.Date.context_today)

    #  Subject
    subject = fields.Char(string='Subject/ጉዳዩ፡-', 
                          default="  የግዥ ትእዛዝ ቁጥር 140539-1 (የትራንስፎርመር ጥገና ) ይመለከታል")
    
    # Editable Body Text (Paragraphs)
    report_header_text = fields.Html(string='Letter Body Content', 
                          default="<p>Our company Wagwago Trading Plc...</p>")
    
    #  
    # We keep line_ids for structured data, but add an HTML field for flexibility if requested
    line_ids = fields.One2many('purchase.request.line', 'request_id', string='Table Lines')
    report_terms = fields.Html(string='Terms & Conditions / Flexible Table Area')

    #  Closing Text
    report_closing_text = fields.Html(string='Closing Text', 
                               default="<p>ለምታደርጉልን መልካም የስራ ትብብር ምስጋናችንን ከወዲሁ እናቀርባለን፡፡</p>")
    
    total_oil = fields.Float(string='Total Oil Consumption', compute='_compute_total_oil')

    #  Signatures
    prepared_by_id = fields.Many2one('res.users', string='Prepared By', readonly=True)
    prepared_date = fields.Date(string='Prepared Date', readonly=True)
    
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Date(string='Approved Date', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status', tracking=True)

    # --- ACTIONS ---
    def action_submit(self):
        self.write({
            'state': 'submitted',
            'prepared_by_id': self.env.user.id,
            'prepared_date': fields.Date.today()
        })

    def action_review(self):
        self.state = 'review'

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approved_date': fields.Date.today()
        })

    def action_print(self):
        self.state = 'sent'
        return self.env.ref('custom_sale_agreement.action_report_purchase_request').report_action(self)

    def action_cancel(self):
        self.state = 'cancel'

    def action_reset_draft(self):
        self.state = 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.oil_consumption')
    def _compute_total_oil(self):
        for rec in self:
            rec.total_oil = sum(rec.line_ids.mapped('oil_consumption'))


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = 'Purchase Request Line'

    request_id = fields.Many2one('purchase.request')
    description = fields.Char(string='Description', required=True)
    serial_number = fields.Char(string='Serial number')
    uom_id = fields.Many2one('uom.uom', string='UM')
    quantity = fields.Float(string='QTY', default=1.0)
    oil_consumption = fields.Float(string='Oil consumption in liter')
    contract_no = fields.Char(string='Contract no')