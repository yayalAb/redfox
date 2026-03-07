# -*- coding: utf-8 -*-
from odoo import models, fields, api
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    
    supervisor_id = fields.Many2one(
        'res.users', 
        string='Task Supervisor', 
        default=lambda self: self.env.user,
        tracking=True,
        help="The person responsible for verifying execution logs for this task."
    )
    # Context: What kind of task is this?
    task_type = fields.Selection([
        ('general', 'General'),
        ('activity', 'Activity Execution'),
        ('financial', 'Financial Execution'),
        ('capex', 'Capex Execution')
    ], string='Task Category', default='general')

    # Links to Specific AOP Lines (Populated by OKR Approval)
    okr_line_id = fields.Many2one('corporate.performance.okr.line', string="Main Key Result")
    aop_activity_id = fields.Many2one('corporate.operating.activity', string="AOP Activity")
    aop_financial_id = fields.Many2one('corporate.operating.financial', string="AOP Financial")
    aop_capex_id = fields.Many2one('corporate.operating.capex', string="AOP Capex")

    # --- THE 3 EXECUTION LOGS ---
    activity_log_ids = fields.One2many('project.task.log.activity', 'task_id', string="Activity Logs")
    financial_log_ids = fields.One2many('project.task.log.financial', 'task_id', string="Financial Logs")
    capex_log_ids = fields.One2many('project.task.log.capex', 'task_id', string="Capex Logs")
    
    total_qty_achieved = fields.Float(string='Total Qty Achieved', compute='_compute_total_progress', store=True)

    @api.depends('activity_log_ids.quantity')
    def _compute_total_progress(self):
        for task in self:
            # Only sum verified records? Or all? Usually verified is safer.
            # Here we sum all for visibility, but you can filter by state='verified'
            task.total_qty_achieved = sum(task.activity_log_ids.mapped('quantity'))
    


# --- 1. ACTIVITY LOG ---
class ProjectLogActivity(models.Model):
    _name = 'project.task.log.activity'
    _description = 'Activity Execution Log'
    _order = 'date desc'

    task_id = fields.Many2one('project.task', required=True, ondelete='cascade')
    date = fields.Date(default=fields.Date.context_today, required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    
    quantity = fields.Float(string='Qty Achieved', required=True)
    description = fields.Char(string='Description')
    
    # Document Reference
    doc_reference = fields.Reference(selection=[
        ('mrp.production', 'Manufacturing Order'),
        ('sale.order', 'Sales Order'),
        ('stock.picking', 'Delivery'),
        ('project.task', 'Task')
    ], string="Evidence")
    
    state = fields.Selection([
        ('draft', 'Pending'),
        ('verified', 'Verified')
    ], default='draft', string="State", tracking=True, readonly=True)

    can_verify = fields.Boolean(compute='_compute_can_verify')

    @api.depends('task_id.supervisor_id', 'state')
    def _compute_can_verify(self):
        current_user = self.env.user
        for rec in self:
            is_supervisor = (rec.task_id.supervisor_id == current_user)
            # Logic: If I am the supervisor AND it is draft -> I can verify
            rec.can_verify = (rec.state == 'draft' and is_supervisor)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProjectLogActivity, self).create(vals_list)
        for rec in records:
            _logger.info(f"DEBUG: Created Activity Log {rec.id} by {self.env.user.name}")
            rec._send_verify_notification()
        return records

    def _send_verify_notification(self):
        """ Notify the Supervisor using message_post (Permanent Record + Inbox Alert) """
        supervisor = self.task_id.supervisor_id
        
        # DEBUG LOGGING
        _logger.info(f"DEBUG: Notification Trigger. Supervisor: {supervisor.name if supervisor else 'None'}, Current User: {self.env.user.name}")

        if supervisor and supervisor != self.env.user:
            msg_body = Markup(
                f"<p>📝 <b>Approval Request</b></p>"
                f"<p><b>{self.user_id.name}</b> reported progress:</p>"
                f"<ul>"
                f"<li><b>Task:</b> {self.task_id.name}</li>"
                f"<li><b>Achieved:</b> {self.quantity}</li>"
                f"</ul>"
                f"<p><i>Please check the execution log tab to verify.</i></p>"
            )

            # Using message_post with partner_ids forces an Inbox Notification
            self.task_id.sudo().message_post(
                body=msg_body,
                message_type='comment', 
                subtype_xmlid='mail.mt_comment',
                partner_ids=[supervisor.partner_id.id], # <--- This is what triggers the bell icon
                author_id=self.user_id.partner_id.id
            )
            _logger.info("DEBUG: Notification Sent to Supervisor")
        else:
            _logger.info("DEBUG: Notification SKIPPED (No supervisor or Self-Notification)")

    def action_verify(self):
        for rec in self:
            rec.write({'state': 'verified'})

            msg = Markup(f"✅ <b>Verified</b><br/>Your achievement of {rec.quantity} has been approved.")

            # Send notification back to employee
            rec.task_id.sudo().message_post(
                body=msg,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[rec.user_id.partner_id.id],
                author_id=self.env.ref('base.partner_root').id # Sent by System/OdooBot
            )

# --- 2. FINANCIAL LOG ---
class ProjectLogFinancial(models.Model):
    _name = 'project.task.log.financial'
    _description = 'Financial Execution Log'
    _order = 'date desc'

    task_id = fields.Many2one('project.task', required=True, ondelete='cascade')
    date = fields.Date(default=fields.Date.context_today, required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)

    amount = fields.Float(string='Amount (ETB)', required=True)
    description = fields.Char(string='Description')
    
    doc_reference = fields.Reference(selection=[
        ('account.move', 'Invoice/Bill'),
        ('account.payment', 'Payment'),
        ('hr.payslip', 'Payslip')
    ], string="Evidence")
    
    state = fields.Selection([
        ('draft', 'Pending'),
        ('verified', 'Verified')
    ], default='draft', string="State")

    can_verify = fields.Boolean(compute='_compute_can_verify')

    @api.depends('task_id.supervisor_id', 'state')
    def _compute_can_verify(self):
        current_user = self.env.user
        for rec in self:
            is_supervisor = (rec.task_id.supervisor_id == current_user)
            rec.can_verify = (rec.state == 'draft' and is_supervisor)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProjectLogFinancial, self).create(vals_list)
        for rec in records: rec._send_verify_notification()
        return records

    def _send_verify_notification(self):
        supervisor = self.task_id.supervisor_id
        if supervisor and supervisor != self.env.user:
            msg_body = Markup(f"💰 <b>Financial Approval</b><br/>User: {self.user_id.name}<br/>Amount: {self.amount}")
            
            self.task_id.sudo().message_post(
                body=msg_body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[supervisor.partner_id.id],
                author_id=self.user_id.partner_id.id
            )

    def action_verify(self):
        for rec in self:
            rec.write({'state': 'verified'})
            rec.task_id.sudo().message_post(
                body=f"✅ Financial entry verified.",
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[rec.user_id.partner_id.id],
                author_id=self.env.ref('base.partner_root').id
            )

# --- 3. CAPEX LOG ---
class ProjectLogCapex(models.Model):
    _name = 'project.task.log.capex'
    _description = 'Capex Execution Log'
    _order = 'date desc'

    task_id = fields.Many2one('project.task', required=True, ondelete='cascade')
    date = fields.Date(default=fields.Date.context_today, required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)

    qty = fields.Float(string='Qty')
    cost = fields.Float(string='Cost (ETB)')
    description = fields.Char(string='Description')
    
    doc_reference = fields.Reference(selection=[
        ('purchase.order', 'Purchase Order'),
        ('account.asset', 'Asset'),
        ('account.move', 'Vendor Bill')
    ], string="Evidence")
    
    state = fields.Selection([
        ('draft', 'Pending'),
        ('verified', 'Verified')
    ], default='draft', string="State")

    can_verify = fields.Boolean(compute='_compute_can_verify')

    @api.depends('task_id.supervisor_id', 'state')
    def _compute_can_verify(self):
        current_user = self.env.user
        for rec in self:
            is_supervisor = (rec.task_id.supervisor_id == current_user)
            rec.can_verify = (rec.state == 'draft' and is_supervisor)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProjectLogCapex, self).create(vals_list)
        for rec in records: rec._send_verify_notification()
        return records

    def _send_verify_notification(self):
        supervisor = self.task_id.supervisor_id
        if supervisor and supervisor != self.env.user:
            msg_body = Markup (f"🏗️ <b>Capex Approval</b><br/>User: {self.user_id.name}<br/>Cost: {self.cost}")
            
            self.task_id.sudo().message_post(
                body=msg_body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[supervisor.partner_id.id],
                author_id=self.user_id.partner_id.id
            )

    def action_verify(self):
        for rec in self:
            rec.write({'state': 'verified'})
            rec.task_id.sudo().message_post(
                body=Markup(f"✅ Capex entry verified."),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                partner_ids=[rec.user_id.partner_id.id],
                author_id=self.env.ref('base.partner_root').id
            )