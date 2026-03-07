from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HVWindingDesign(models.Model):
    _name = 'hv.winding.design'

    # name = fields.Char(string="Name", compute='_compute_name', store=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product')
    edge_insulation = fields.One2many('hv.winding.edge.paper', 'hv_design', string='HV Winding Edge Paper')
    interlayer_insulation = fields.One2many('hv.winding.interlayer.insulation', 'hv_design', string='HV Winding Interlayer Insulation')
    turn_arrangement = fields.One2many('hv.turn.arrangement', 'hv_design')
    winding_type = fields.Char()
    connection = fields.Char()
    turns_per_phase = fields.Integer(string='Turns per phase', )
    bare_conductor_size = fields.Char()
    conductor_insulation = fields.Float(string='Conductor Insulation')
    covered_conductor_size = fields.Float()
    conductor_placement = fields.Char()
    discs_per_phase = fields.Integer()
    turns_per_disc = fields.Integer()
    layers_per_disc = fields.Integer()
    turns_number_per_layer_per_coil = fields.Char()
    inter_layer_insulation = fields.Char()
    end_packing = fields.Float()
    axial_length = fields.Float()
    coil_height = fields.Float()
    internal_diameter = fields.Float()
    outer_diameter = fields.Float()
    copper_weight_per_phase = fields.Float()
    resistance_per_phase = fields.Float()
    taps = fields.One2many('tap.info', 'hv_design')
    state = fields.Selection([
        ('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='draft')
    rejected_by = fields.Many2one('res.users')
    rejection_reason = fields.Text(string='Rejection Reason')


    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    # def action_open_service_request(self):
    #     self.ensure_one()

    #     return {
    #         'name': 'Service Request',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'service.request',
    #         'res_id': self.service_request.id
    #     }

class TapInfo(models.Model):
    _name = 'tap.info'

    hv_design = fields.Many2one('hv.winding.design', )
    tap_number = fields.Char()
    connection_point = fields.Char()
    turn_numbers = fields.Integer(string='Number of Turns', )

class HvDesignWizard(models.TransientModel):
    _name = 'hv.design.reject.wizard'
    _description = 'Hv Design Reject Wizard'

    hv_design = fields.Many2one(
        'hv.winding.design', string='Hv Design', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', )
    rejected_by = fields.Many2one(
        'res.users', string='Rejected By', readonly=True)

    def action_confirm_reject(self):
        self.ensure_one()
        hv_design = self.hv_design
        user = self.env.user

        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason.'))

        hv_design.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
            'rejected_by': user.id,
        })
        return True

class HvTurnArrangement(models.Model):
    _name = 'hv.turn.arrangement'

    hv_design = fields.Many2one('hv.winding.design')
    sequence = fields.Integer(
        string="Sequence",
        readonly=True,
        default=0,
        copy=False
    )
    
    layers_turn = fields.Integer(string="Turns in this Layer")
    
    turns_sum = fields.Integer(
        string="Cumulative Turns Sum",
        readonly=True,
        help="Sum of 'Turns in this Layer' from all previous records."
    )

    @api.model_create_multi
    def create(self, vals_list):
        existing_records_data = self.search_read([], ['layers_turn'])
        current_total_sum = sum(rec['layers_turn'] for rec in existing_records_data)

        for vals in vals_list:

            vals['sequence'] = self.env['ir.sequence'].next_by_code('hv.turn.arrangement.sequence') or 0

            vals['turns_sum'] = current_total_sum
            current_total_sum += vals.get('layers_turn', 0)


        return super(HvTurnArrangement, self).create(vals_list)

class HvWindingEdgePaper(models.Model):
    _name = 'hv.winding.edge.paper'

    hv_design = fields.Many2one('hv.winding.design', required=True)
    layer = fields.Integer()
    th = fields.Float()
    w1 = fields.Integer(string='W1')
    w2 = fields.Integer(string='W2')
    length = fields.Integer()
    number_l = fields.Integer(string='No./L')
    number_ph = fields.Integer(string='No./ph')
    number_tr = fields.Integer(string='NO./tr')

class HvWindingEdgePaper(models.Model):
    _name = 'hv.winding.interlayer.insulation'

    hv_design = fields.Many2one('hv.winding.design', required=True)
    layer = fields.Integer()
    th = fields.Float()
    width = fields.Integer()
    length = fields.Integer()
    number_l = fields.Integer(string='No./L')
    number_ph = fields.Integer(string='No./ph')
    number_tr = fields.Integer(string='NO./tr')



