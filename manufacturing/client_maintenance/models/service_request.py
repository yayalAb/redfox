from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ServiceRequest(models.Model):
    _name = 'service.request'

    name = fields.Char(string='Reference', copy=False,
                       required=True, readonly=True, default=lambda self: 'New')
    date = fields.Date(string='Date', required=True)
    requesting_department = fields.Many2one(
        'hr.department', string='Service Requesting Dept', required=True)
    providing_department = fields.Many2one(
        'hr.department', string='Service Providing Dept')
    service_type = fields.Many2one('service.type')
    product_id = fields.Many2one('product.product', string="Item")
    quantity = fields.Integer(string='Quantity', required=True)
    requesting_person = fields.Many2one(
        'res.users', string='Service Requesting Person', default=lambda self: self.env.user)
    requester_position = fields.Char(
        related='requesting_person.employee_id.job_title', string='Position', readonly=True)
    description = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('completed', 'Completed'), ('rejected', 'Rejected')],
        default='draft', required=True)
    
    measurement_form = fields.One2many('measurement.log', 'service_request')
    measurement_state = fields.Selection(related='measurement_form.state')

    project_id = fields.Many2one('project.project', string='Project', readonly=True, copy=False)

    rejected_by = fields.Many2one('res.users', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    fault_category = fields.Many2one('fault.category', string='Fault Category')
    fault_level = fields.Selection([
        ('level_1', 'Level 1'), ('level_2', 'Level 2'), ('level_3', 'Level 3'), ('level_4', 'Level 4')])

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'service.request') or 'New'
        res = super(ServiceRequest, self).create(vals)
        return res
    
    # @api.constrains('measurement_form')
    # def _check_measurement_form(self):
    #     for rec in self:
    #         measurements = self.env['measurement.log'].search_count([])
            

    def action_submit(self):
        for req in self:
            if not req.project_id:
                project = self.env['project.project'].create({
                    'name': f"SR: {req.name}",
                    'allow_task_dependencies': True,
                    'date_start': fields.Date.today(),
                })
                req.project_id = project.id
            req.write({'state': 'submitted'})
        return True

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_done(self):
        self.write({'state': 'completed'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_measurement(self):
        self.ensure_one()

        return {
            'name': 'Measurement Form',
            'type': 'ir.actions.act_window',
            'res_model': 'measurement.log',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                    'default_service_request': self.id,
            }
        }

    def action_open_measurement_form(self):
        self.ensure_one()

        return {
            'name': 'Measurement Form',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'measurement.log',
            'domain': [('service_request', '=', self.id)],
        }




class ServiceType(models.Model):
    _name = 'service.type'

    name = fields.Char(required=True)


class FaultCategory(models.Model):
    _name = 'fault.category'

    name = fields.Char(required=True)


class ServiceRequestRejectWizard(models.TransientModel):
    _name = 'service.request.reject.wizard'
    _description = 'Service Request Reject Wizard'

    service_request = fields.Many2one(
        'service.request', string='Requisition', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)
    rejected_by = fields.Many2one(
        'res.users', string='Rejected By', readonly=True)

    def action_confirm_reject(self):
        self.ensure_one()
        service_request = self.service_request
        user = self.env.user

        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason.'))

        service_request.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
            'rejected_by': user.id,
        })
        return True
