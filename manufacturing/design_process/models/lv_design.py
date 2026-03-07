from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class LVWindingDesign(models.Model):
    _name = 'lv.winding.design'

    product_tmpl_id = fields.Many2one('product.template', string='Product')
    edge_insulation = fields.One2many('lv.winding.edge.paper', 'lv_design', string='LV Winding Edge Paper')
    interlayer_insulation = fields.One2many('lv.winding.interlayer.insulation', 'lv_design', string='LV Winding Interlayer Insulation')
    connection_type = fields.Char()
    connection = fields.Char()
    turns_per_phase = fields.Integer(string='No. of turns per phase')
    conductor_type = fields.Char()
    bare_conductor_size = fields.Char()
    covering = fields.Float()
    insulated_conductor_size = fields.Char()
    conductor_arrangement = fields.Char()
    parallel_conductors_number = fields.Integer()
    transposition = fields.Integer()
    taping = fields.Char()
    layers_number = fields.Integer()
    turn_numbers_per_layer_per_coil = fields.Char()
    inter_layer_insulation = fields.Float()
    gap_clearance_between_core_lv = fields.Float()
    internal_diameter = fields.Float()
    outer_diameter = fields.Float()
    end_insulation = fields.Char()
    radial_length = fields.Float()
    axial_length = fields.Float()
    copper_weight_per_phase = fields.Float()
    resistance_per_phase = fields.Float()
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

    def action_open_service_request(self):
        self.ensure_one()

        return {
            'name': 'Service Request',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'service.request',
            'res_id': self.service_request.id
        }


class LvWindingEdgePaper(models.Model):
    _name = 'lv.winding.edge.paper'

    lv_design = fields.Many2one('lv.winding.design', required=True)
    layer = fields.Integer()
    th = fields.Float()
    w1 = fields.Integer(string='W1')
    w2 = fields.Integer(string='W2')
    length = fields.Integer()
    number_l = fields.Integer(string='No./L')
    number_ph = fields.Integer(string='No./ph')
    number_tr = fields.Integer(string='NO./tr')

class LvWindingEdgePaper(models.Model):
    _name = 'lv.winding.interlayer.insulation'

    lv_design = fields.Many2one('lv.winding.design', required=True)
    layer = fields.Integer()
    th = fields.Float()
    width = fields.Integer()
    length = fields.Integer()
    number_l = fields.Integer(string='No./L')
    number_ph = fields.Integer(string='No./ph')
    number_tr = fields.Integer(string='NO./tr')


class LvDesignWizard(models.TransientModel):
    _name = 'lv.design.reject.wizard'
    _description = 'Lv Design Reject Wizard'

    lv_design = fields.Many2one(
        'lv.winding.design', string='Lv Design', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', )
    rejected_by = fields.Many2one(
        'res.users', string='Rejected By', readonly=True)

    def action_confirm_reject(self):
        self.ensure_one()
        lv_design = self.lv_design
        user = self.env.user

        if not self.rejection_reason:
            raise UserError(_('Please provide a rejection reason.'))

        lv_design.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
            'rejected_by': user.id,
        })
        return True
