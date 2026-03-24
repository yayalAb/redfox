# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError

class TenderStage(models.Model):
    _name = 'tender.stage'
    _description = 'Tender Stages'
    _order = 'name desc'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    is_won = fields.Boolean(string='Is Won Stage')
    is_lost = fields.Boolean(string='Is Lost Stage')
    is_submission = fields.Boolean(string="Is Submission Stage")
    fold = fields.Boolean(string='Folded in Kanban',
                          help='This stage is folded in the kanban view when there are no records in it.')
                        

class TenderRequest(models.Model):
    _name = 'tender.request'
    _description = 'Tender Participation Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Kanban Stage
    stage_id = fields.Many2one(
        'tender.stage', string='Stage', index=True, tracking=True,
        readonly=False, store=True, copy=False,
        ondelete='restrict',
        group_expand='_read_group_stage_ids',
        default=lambda self: self._default_stage_id())

    # Strict Workflow State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),             
        ('tech_prep', 'Tech Doc Prep'),        
        ('tech_review', 'Tech Doc Review'),     
        ('submission', 'Submitted to Client'),  
        ('won', 'Won'),                        
        ('lost', 'Lost'),                      
        ('rejected', 'Rejected (Internal)'),    
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, readonly=True)

    name = fields.Char(string='Tender Reference No', required=True, copy=False,
                       readonly=False, index=True, default=lambda self: ('New')) 
    customer_id = fields.Many2one(
        'res.partner', string='Purchaser Name', required=True, tracking=True)
    title = fields.Char(string='Tender Title', required=True, tracking=True)

    responsible_id = fields.Many2one(
        'res.users', string='Responsible Salesperson', tracking=True, 
        help="Person assigned to prepare the technical documents."
    )

    rejection_reason = fields.Text(string="Reason for Rejection", tracking=True)
    tech_refuse_comments = fields.Text(string="Tech Doc Review Comments", tracking=True)

    technical_document_ids = fields.Many2many('ir.attachment', 'tender_tech_doc_rel', 'tender_id', 'attachment_id', string="Technical Documents")
    
    submission_deadline = fields.Datetime(
        string=' Deadline', required=True, tracking=True)
    decision_date = fields.Date(string='Expected Decision Date', tracking=True)
    
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Currency')
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company)
    tender_value = fields.Monetary(
        string='Total Tender Value', compute='_compute_tender_value', store=True)

    tender_line_ids = fields.One2many(
        'tender.request.line', 'tender_id', string='Tender Lines')
    goods_description = fields.Char(string='Goods Description')
    supplier_id = fields.Many2one('res.partner', string="Preferred Supplier")
    
    # Corrected naming convention (was check_list_id)
    checklist_ids = fields.One2many(
        'tender.checklist', 'tender_id', string="Tender Requirements")
    
    # NEW FIELD: Text alternative for Bid Requirements
    requirements_text = fields.Html(
        string='Requirements Details', 
        help="Use this to paste requirements directly."
    )
    winning_price = fields.Monetary(string='Winning Price')

    # Attachments
    tender_document = fields.Binary(string='Tender Document', attachment=True)
    tender_document_ids = fields.Many2many('ir.attachment', 'tender_req_doc_rel', 'tender_id', 'attachment_id', string='Tender Request Documents')
    bid_doc_cost = fields.Float(string='Bid Doc Cost')

    # Related Company Documents
    co_business_license = fields.Binary(related='company_id.business_license', string="Business License", readonly=True)
    co_commercial_reg = fields.Binary(related='company_id.commercial_registration', string="Commercial Registration", readonly=True)
    co_tin_cert = fields.Binary(related='company_id.tin_document', string="TIN Certificate", readonly=True)
    co_vat_cert = fields.Binary(related='company_id.vat_document', string="VAT Certificate", readonly=True)
    co_tax_clearance = fields.Binary(related='company_id.tax_clearance', string="Tax Clearance", readonly=True)
    co_egp_reg = fields.Binary(related='company_id.egp_registration', string="EGP Registration", readonly=True)
    co_experience_letters = fields.Many2many(
        related='company_id.experience_letters',
        string="Previous Experience & Testimonials",
    )
    co_audit_report = fields.Binary(related='company_id.audit_report', string="Audit Report", readonly=True)
    co_financial_standing = fields.Binary(related='company_id.financial_standing', string="Financial Standing", readonly=True)

    # Outcome Fields
    won_date = fields.Date(string="Date Won", readonly=True)
    lost_reason_id = fields.Many2one('tender.lost.reason', string='Reason for Loss', tracking=True)
    lost_reason_notes = fields.Text(string="Loss Details")
    
    # Smart Button Links
    agreement_id = fields.Many2one('sale.agreement', string='Related Agreement', readonly=True, copy=False)
    agreement_count = fields.Integer(compute='_compute_agreement_count', string="Agreement Count")
    warranty_count = fields.Integer(compute='_compute_warranty_count', string="Warranty Letter Count")
    power_attorney_count = fields.Integer(compute='_compute_power_attorney_count', string="Power of Attorney Count")
    bid_bond_count = fields.Integer(compute='_compute_bid_bond_count', string="Bid Bond Count")

    @api.model
    def _default_stage_id(self):
        """Set default stage to the one with the lowest sequence"""
        return self.env['tender.stage'].search([], order='sequence asc', limit=1)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None):
        return stages.search([], order=order)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('tender.request') or 'New'
        return super(TenderRequest, self).create(vals_list)

    def write(self, vals):
        """ Keeps the Kanban stage synced with the strict state """
        res = super(TenderRequest, self).write(vals)
        if 'stage_id' in vals:
            stage = self.env['tender.stage'].browse(vals['stage_id'])
            if stage.is_won and self.state != 'won':
                self.state = 'won'
                self.won_date = fields.Date.context_today(self)
            elif stage.is_lost and self.state != 'lost':
                self.state = 'lost'
            elif stage.is_submission and self.state != 'submission':
                self.state = 'submission'
        return res
    

    @api.depends('tender_line_ids.subtotal')
    def _compute_tender_value(self):
        for tender in self:
            tender.tender_value = sum(tender.tender_line_ids.mapped('subtotal'))

    # --- STRICT WORKFLOW ACTIONS ---

    def action_submit_internal(self):
        """ Send for internal management review """
        for tender in self:
            if not tender.customer_id:
                raise ValidationError("You must select a customer.")
            tender.state = 'review'
            # Auto-move Kanban stage if applicable
            next_stage = self.env['tender.stage'].search([('sequence', '>', self.stage_id.sequence)], order='sequence asc', limit=1)
            if next_stage:
                tender.stage_id = next_stage.id
    def action_bid_fit(self):
        """ STEP 2a: Review -> Tech Prep (Bid Fits) """
        for tender in self:
            if not tender.responsible_id:
                raise ValidationError(_("Please assign a Responsible Salesperson before marking the bid as fit."))
            tender.state = 'tech_prep'

    def action_bid_reject(self):
        """ STEP 2b: Review -> Rejected (Internal) """
        self.ensure_one()
        return self._open_refuse_wizard('bid')
    
    def action_submit_tech_docs(self):
        """ STEP 3: Tech Prep -> Tech Review """
        for tender in self:
            tender.state = 'tech_review'

    def action_approve_tech_docs(self):
        """ STEP 4a: Tech Review -> Submitted to Client """
        for tender in self:
            tender.state = 'submission'
            # Move Kanban column automatically if configured
            sub_stage = self.env['tender.stage'].search([('is_submission', '=', True)], limit=1)
            if sub_stage:
                tender.stage_id = sub_stage.id

    def action_refuse_tech_docs(self):
        """ STEP 4b: Tech Review -> Tech Prep (Returned for revision) """
        self.ensure_one()
        return self._open_refuse_wizard('tech')

    def action_submit_to_client(self):
        """ Mark as officially submitted to the client """
        for tender in self:
            # tender.state = 'submission'
            sub_stage = self.env['tender.stage'].search([('is_submission', '=', True)], limit=1)
            if sub_stage:
                tender.stage_id = sub_stage.id

    def action_win(self):
        for tender in self:
            tender.state = 'won'
            tender.won_date = fields.Date.context_today(self)
            won_stage = self.env['tender.stage'].search([('is_won', '=', True)], limit=1)
            if won_stage:
                tender.stage_id = won_stage.id

    def action_lose(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Lost Reason',
            'res_model': 'tender.lost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tender_id': self.id}
        }
        
    def action_reset_draft(self):
        for tender in self:
            tender.state = 'draft'
            first_stage = self.env['tender.stage'].search([], order='sequence asc', limit=1)
            if first_stage:
                tender.stage_id = first_stage.id
    def _open_refuse_wizard(self, refuse_type):
        """ Helper to open the wizard for either Bid Rejection or Tech Doc Revision """
        return {
            'name': _('Provide Feedback / Rejection Reason'),
            'type': 'ir.actions.act_window',
            'res_model': 'tender.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tender_id': self.id,
                'default_refuse_type': refuse_type
            }
        }

    # --- DOCUMENTS & AGREEMENTS (Kept Original Logic) ---

    def _compute_agreement_count(self):
        for tender in self:
            tender.agreement_count = self.env['sale.agreement'].search_count([('tender_id', '=', tender.id)])

    def action_create_agreement(self):
        self.ensure_one()
        agreement_lines = [(0, 0, {
            'product_id': line.product_id.id,
            'description': line.description,
            'quantity': line.quantity,
            'uom_id': line.product_id.uom_id.id,
            'unit_price': line.unit_price,
        }) for line in self.tender_line_ids]

        agreement = self.env['sale.agreement'].create({
            'name': self.title,
            'partner_id': self.customer_id.id,
            'tender_id': self.id,
            'line_ids': agreement_lines,
            'start_date': fields.Date.today(),
            'end_date': self.submission_deadline,
            'source_from': 'tender',
        })
        self.agreement_id = agreement.id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agreement',
            'res_model': 'sale.agreement',
            'res_id': agreement.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_agreements(self):
        return {
            'name': 'Related Agreements',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'sale.agreement',
            'domain': [('tender_id', '=', self.id)],
        }

    @api.constrains('submission_deadline', 'decision_date')
    def _check_dates(self):
        for tender in self:
            if tender.submission_deadline and tender.submission_deadline < fields.Datetime.now():
                raise ValidationError("The Submission Deadline cannot be in the past.")
            if tender.decision_date and tender.submission_deadline and tender.decision_date < tender.submission_deadline.date():
                raise ValidationError("The Expected Decision Date must be after the Submission Deadline.")
            
    def _compute_warranty_count(self):
        for tender in self:
            tender.warranty_count = self.env['bid.warranty.letter'].search_count([('tender_id', '=', tender.id)])
    
    def _compute_power_attorney_count(self):
        for tender in self:
            tender.power_attorney_count = self.env['bid.power.attorney'].search_count([('tender_id', '=', tender.id)])

    def action_create_warranty_letter(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Warranty Letter',
            'res_model': 'bid.warranty.letter',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_tender_id': self.id,
                'default_partner_id': self.customer_id.id,
                'default_tender_reference': self.name,
                'default_date_issue': fields.Date.context_today(self),
                'default_company_id': self.company_id.id,
            }
        }
    
    def action_view_warranty_letters(self):
        self.ensure_one()
        return {
            'name': 'Warranty Letter',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'bid.warranty.letter',
            'domain': [('tender_id', '=', self.id)],
            'context': {'default_tender_id': self.id}
        }
    
    def action_create_power_of_attorney(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Power of Attorney',
            'res_model': 'bid.power.attorney',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tender_id': self.id,
                'default_company_id': self.company_id.id,
                'default_procuring_entity_id': self.customer_id.id, 
                'default_bid_reference': self.name,
                'default_tender_description': self.title, 
                'default_date_issue': fields.Date.context_today(self),
            }
        }

    def action_view_power_of_attorneys(self):
        self.ensure_one()
        return {
            'name': 'Power of Attorney Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'bid.power.attorney',
            'view_mode': 'tree,form',
            'domain': [('tender_id', '=', self.id)],
            'context': {'default_tender_id': self.id}
        }
    
    def _compute_bid_bond_count(self):
        for tender in self:
            tender.bid_bond_count = self.env['tender.bid.bond'].search_count([('tender_id', '=', tender.id)])

    def action_create_bid_bond(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Bid Bond',
            'res_model': 'tender.bid.bond',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_tender_id': self.id,
                'default_beneficiary_id': self.customer_id.id, 
                'default_tender_ref_no': self.name, 
                'default_goods_description': self.goods_description or self.title,
                'default_validity_start_date': self.submission_deadline.date() if self.submission_deadline else fields.Date.context_today(self),
                'default_currency_id': self.currency_id.id,
            }
        }

    def action_view_bid_bonds(self):
        self.ensure_one()
        return {
            'name': 'Bid Bonds',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'tender.bid.bond',
            'domain': [('tender_id', '=', self.id)],
            'context': {'default_tender_id': self.id}
        }


class TenderRequestLine(models.Model):
    _name = 'tender.request.line'
    _description = 'Products offered in a Tender'

    tender_id = fields.Many2one(
        'tender.request', string='Tender Request', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Product', required=True)
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price')
    subtotal = fields.Monetary(
        string='Subtotal', compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='tender_id.currency_id')

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.unit_price = self.product_id.list_price


class TenderLostReason(models.Model):
    _name = 'tender.lost.reason'
    _description = 'Reason for Losing a Tender'
    name = fields.Char(string='Reason', required=True, translate=True)
    active = fields.Boolean(default=True)


class TenderLostWizard(models.TransientModel):
    _name = 'tender.lost.wizard'
    _description = 'Wizard to select the reason for losing a tender'
    
    tender_id = fields.Many2one('tender.request', string="Tender", readonly=True)
    lost_reason_id = fields.Many2one('tender.lost.reason', string='Reason for Loss', required=True)
    lost_reason_notes = fields.Text(string="Loss Details")

    def action_confirm_lost(self):
        self.ensure_one()
        if self.tender_id:
            lost_stage = self.env['tender.stage'].search([('is_lost', '=', True)], limit=1)
            vals = {
                'lost_reason_id': self.lost_reason_id.id,
                'lost_reason_notes': self.lost_reason_notes,
                'state': 'lost',
            }
            if lost_stage:
                vals['stage_id'] = lost_stage.id
            self.tender_id.write(vals)
        return {'type': 'ir.actions.act_window_close'}
    

class TenderChecklist(models.Model):
    _name = 'tender.checklist'
    _description = 'Tender Checklists'

    tender_id = fields.Many2one('tender.request', string='Tender Request', required=True, ondelete='cascade')
    name = fields.Char(string='Checklist Name', required=True)
    description = fields.Text()
    is_done = fields.Boolean(string='Done')
    is_mandatory = fields.Boolean(string='Mandatory')

class TenderRefuseWizard(models.TransientModel):
    _name = 'tender.refuse.wizard'
    _description = 'Tender Refusal/Revision Wizard'

    tender_id = fields.Many2one('tender.request', string="Tender", required=True, readonly=True)
    refuse_type = fields.Selection([
        ('bid', 'Reject Entire Bid'),
        ('tech', 'Return Tech Docs for Revision')
    ], string="Refusal Type", required=True)
    
    refuse_reason = fields.Text(string="Comments / Reason", required=True)

    def action_confirm_refuse(self):
        self.ensure_one()
        if self.refuse_type == 'bid':
            # Internal rejection
            self.tender_id.write({
                'state': 'rejected',
                'rejection_reason': self.refuse_reason
            })
        elif self.refuse_type == 'tech':
            # Send back to prep stage
            self.tender_id.write({
                'state': 'tech_prep',
                'tech_refuse_comments': self.refuse_reason
            })
        return {'type': 'ir.actions.act_window_close'}