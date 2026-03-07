from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

class MeasurementLog(models.Model):
    _name = 'measurement.log'

    name = fields.Char(string="Name", compute='_compute_name', store=True)
    
    # Transformer Information
    service_request = fields.Many2one('service.request', ondelete='cascade')
    transformer_kva = fields.Float(string='KVA')
    transformer_kv = fields.Float(string='KV')
    job_number = fields.Char(string='Job No.')
    serial_number = fields.Char(string='Serial No.')
    manufacturer = fields.Char(string='Manufacturer')
    manufacturing_year = fields.Date(string='Manufacturing Year')

    # Core
    core_type = fields.Selection([
        ('round', 'Round'), ('rectangular', 'Rectangular'), ('oval', 'Oval')])
    core_diameter = fields.Float(string='Core Diameter')
    limb_center = fields.Float(string='Limb Center')
    window_height = fields.Float(string='Window Height')

    # LV Winding
    turns_per_layer = fields.Integer(string='Turns Per Layer')
    lv_internal_diameter = fields.Float(string='Internal Diameter')
    lv_external_diameter = fields.Float(string='External Diameter')
    lv_axial_length = fields.Float(string='Axial Length')
    # LV Edge Paper
    w1 = fields.Char(string='W1')
    w2 = fields.Char(string='W2')
    coil_height = fields.Float(string='Coil Height')

    # copper_size
    rectangular_w = fields.Float(string='Rectangular W')
    rectangular_d = fields.Float(string='Rectangular D')
    foil_t = fields.Float(string='Foil T')
    copper_placement = fields.Char(string='Copper Placement')
    winding_direction = fields.Char(string='Winding Direction')

    # Hv Winding
    tap_turns = fields.Integer()
    hv_internal_diameter = fields.Float(string='Internal Diameter')
    hv_external_diameter = fields.Float(string='External Diameter')
    hv_axial_length = fields.Float(string='Axial Length')
    lv_edge_paper = fields.Char(string='LV Edge Paper')
    # Coil Height
    disc1 = fields.Float(string='Disc1')
    disc2 = fields.Float(string='Disc2')
    disc3 = fields.Float(string='Disc3')
    disc4 = fields.Float(string='Disc4')
    disc5 = fields.Float(string='Disc5')
    disc6 = fields.Float(string='Disc6')
    copper_s1 = fields.Float(string='S1')
    copper_s2 = fields.Float(string='S2')
    copper_s3 = fields.Float(string='S3')
    number_of_coils = fields.Integer(string='No. of coils that need design')
    
    insulation_lines = fields.One2many('insulation.log', 'measurement_log')
    
    #additional Info
    measured_by = fields.Many2one('hr.employee')
    approved_by = fields.Many2one('hr.employee')
    rejected_by = fields.Many2one('res.users')
    rejection_reason = fields.Text(string='Rejection Reason')
    date = fields.Date(default=fields.Date.context_today)
    
    additional = fields.Text(string='Additional Note')
    state = fields.Selection([
        ('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft')
    
    @api.depends('service_request')
    def _compute_name(self):
        for record in self:
            if record.service_request:
                record.name = f"LV Design for {record.service_request.name}"
            else:
                record.name = "New LV Design"

    @api.constrains('service_request')
    def _check_unique_for_service_request(self):
        for record in self:
            if not record.service_request:
                continue
            
            existing_records = self.search_count([
                ('service_request', '=', record.service_request.id),
                ('state', '!=', 'rejected'),
                ('id', '!=', record.id)
            ])
            
            if existing_records > 0:
                raise ValidationError(
                    "This Service Request already has a Measurement form. Only one is allowed."
                )


    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_open_service_request(self):
        self.ensure_one()

        return {
            'name': 'Service Request',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'service.request',
            'res_id': self.service_request.id
        }


class InsulationLog(models.Model):
    _name = 'insulation.log'

    measurement_log = fields.Many2one('measurement.log')
    category = fields.Selection([
        ('between_lv_hv', 'B/n LV & HV'),
        ('between_discs', 'B/n Discs'),
        ('between_winding_core',
         'B/n Winding & Core'),
        ('between_core_lv', 'B/n Core & LV')
    ])
    insulation_type = fields.Char()
    ntxwxh = fields.Char(string='N(TXWXH)')
    place = fields.Selection([
        ('hv_winding', 'In HV Winding'), ('between_phases', 'B/n Phases')
    ])

class MeasurementFormRejectWizard(models.TransientModel):
    _name = 'measurement.form.reject.wizard'
    _description = 'Measurement Form Reject Wizard'

    measurement_form = fields.Many2one(
        'measurement.log', string='Measurement Form', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    rejected_by = fields.Many2one(
        'res.users', string='Rejected By', readonly=True)

    def action_confirm_reject(self):
        self.ensure_one()
        measurement_form = self.measurement_form
        user = self.env.user

        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason.'))

        measurement_form.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
            'rejected_by': user.id,
        })
        return True
    
    
    