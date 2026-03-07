from odoo import models, fields, api, _
from odoo.exceptions import UserError


FAT_TEST_TYPES_TECHNICAL = [
    'fat_step1_insulation',
    'fat_step2_ratio',
    'fat_step3_no_load',
    'fat_step4_load_loss',
    'fat_step5_winding',
    'fat_step6_separate',
    'fat_step7_induced',
]


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    fat_check_count = fields.Integer(
        compute='_compute_fat_check_count',
        string="FAT Checks"
    )

    fat_pass = fields.Boolean(string='FAT pass', compute='_check_fat_pass')
    elpa_approved = fields.Boolean(
        default=False, 
        string='ELPA Approval',
        copy=False,
    )
    date_elpa_approved = fields.Date()

    rated_capacity = fields.Float()
    serial_number = fields.Char()
    pri_rated_voltage = fields.Float()
    sec_rated_voltage = fields.Float()
    pri_rated_current = fields.Float()
    sec_rated_current = fields.Float()
    test_number = fields.Integer()
    vector_group = fields.Char()
    frequency = fields.Float()
    iec = fields.Char()
    cooling = fields.Char()

    @api.depends('check_ids.quality_state')
    def _check_fat_pass(self):
        for production in self:
            if not production.check_ids:
                production.fat_pass = False
                continue

            all_passed = all(check.quality_state == 'pass' for check in production.check_ids)
            production.fat_pass = all_passed



    def action_elpa_approve(self):
        self.ensure_one()
        if not self.fat_pass:
            raise UserError(_(
                "ELPA Approval cannot be granted because not all required Factory Acceptance Tests have passed. "
                "Please review the FAT Checks and ensure they are all in the 'Passed' state."
            ))
        self.write({'elpa_approved': True, 'date_elpa_approved': fields.Date.today()})
        self.check_ids.write({'elpa_approved': True})


    def _compute_fat_check_count(self):
        for production in self:
            production.fat_check_count = self.env['quality.check'].search_count([
                ('production_id', '=', production.id),
                ('test_type', 'in', FAT_TEST_TYPES_TECHNICAL)
            ])

    def action_open_fat_checks(self):
        self.ensure_one()
        return {
            'name': 'Factory Acceptance Tests',
            'type': 'ir.actions.act_window',
            'res_model': 'quality.check',
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.check_ids.ids)],
            'context': {'default_production_id': self.id}
        }

                
    def print_fat_report(self):
        self.ensure_one()
        if not self.elpa_approved:
            raise UserError(_("The FAT report can only be printed after ELPA approval."))
        return self.env.ref('custom_manufacturing.action_report_fat').report_action(self)

    def get_fat_data(self):
        self.ensure_one()
        data = {
            'step1': None, 'step2': None, 'step3': None, 'step4': None,
            'step5': None, 'step6': None, 'step7': None,
        }
        
        for check in self.check_ids:
            if check.fat_name == 'fat_step1_insulation':
                data['step1'] = check.fat_step1_id
            elif check.fat_name == 'fat_step2_ratio':
                data['step2'] = check.fat_step2_id
            elif check.fat_name == 'fat_step3_no_load':
                data['step3'] = check.fat_step3_id
            elif check.fat_name == 'fat_step4_load_loss':
                data['step4'] = check.fat_step4_id
            elif check.fat_name == 'fat_step5_winding':
                data['step5'] = check.fat_step5_id
            elif check.fat_name == 'fat_step6_separate':
                data['step6'] = check.fat_step6_id
            elif check.fat_name == 'fat_step7_induced':
                data['step7'] = check.fat_step7_id
                
        return data
    
    
    def button_mark_done(self):
        for production in self:
            pending_checks = production.check_ids.filtered(lambda x: x.quality_state != 'pass')
            
            if pending_checks:
                raise UserError(_(
                    "You cannot mark this Manufacturing Order as Done.\n"
                    "There are pending Quality Checks that must be processed first."
                ))

        return super(MrpProduction, self).button_mark_done()