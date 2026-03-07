# custom_quality_fat_plan/models/quality_check.py

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .quality_point_plan import FAT_TEST_TYPES_SELECTION

FAT_TEST_TYPE_TO_FIELD_MAP = {
    'fat_step1_insulation': 'fat_step1_id',
    'fat_step2_ratio': 'fat_step2_id',
    'fat_step3_no_load': 'fat_step3_id',
    'fat_step4_load_loss': 'fat_step4_id',
    'fat_step5_winding': 'fat_step5_id',
    'fat_step6_separate': 'fat_step6_id',
    'fat_step7_induced': 'fat_step7_id', 
}


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    fat_name = fields.Selection(FAT_TEST_TYPES_SELECTION)
    elpa_approved = fields.Boolean(string="ELPA Approved", default=False, copy=False)
    
    fat_step1_id = fields.One2many(
        'fat.step1.insulation', 'check_id', string='Insulation Data')
    fat_step2_id = fields.One2many(
        'fat.step2.ratio', 'check_id', string='Ratio Test Data')
    fat_step3_id = fields.One2many(
        'fat.step3.no.load', 'check_id', string='NO Load Loss Data')
    fat_step4_id = fields.One2many(
        'fat.step4.load.loss', 'check_id', string='Load Loss Data')
    fat_step5_id = fields.One2many(
        'fat.step5.winding', 'check_id', string='Winding Resistance Data')
    fat_step6_id = fields.One2many(
        'fat.step6.separate', 'check_id', string='Separate Source Data')
    fat_step7_id = fields.One2many(
        'fat.step7.induced', 'check_id', string='Induced Overvoltage Data')

    @api.model_create_multi
    def create(self, vals_list): 
        records = super().create(vals_list)
        for record in records:
            if record.fat_name in FAT_TEST_TYPE_TO_FIELD_MAP:
                field_name = FAT_TEST_TYPE_TO_FIELD_MAP[record.fat_name]
                model_name = self[field_name].browse()._name
                if not getattr(record, field_name):
                    self.env[model_name].create({'check_id': record.id})
        return records

    def _update_fat_instance_state(self, new_state):
        for check in self:
            if check.fat_name in FAT_TEST_TYPE_TO_FIELD_MAP:
                field_name = FAT_TEST_TYPE_TO_FIELD_MAP[check.fat_name]
                fat_instance = getattr(check, field_name)
                if fat_instance:
                    fat_instance.write({'state': new_state})

    def do_pass(self):
        for check in self:
            open_alerts = self.env['quality.alert'].search([
                ('check_id', '=', check.id),
                ('stage_id.done', '!=', True)
            ])
            if open_alerts:
                raise UserError(_(
                    "You cannot pass this quality check because there are open quality alert associated with it. Please resolve the alert(s) first."
                ))
            res = super(QualityCheck, self).do_pass()
            self._update_fat_instance_state('passed')
            return res


    def do_fail(self):
        res = super(QualityCheck, self).do_fail()
        self._update_fat_instance_state('failed')

        alert_vals_list = []
        for check in self:
            # Prepare values for the quality alert
            alert_vals = {
                'check_id': check.id,
                'product_id': check.product_id.id,
                'product_tmpl_id': check.product_id.product_tmpl_id.id,
                'lot_id': check.lot_id.id,
                'production_id': check.production_id.id,
                'workorder_id': check.workorder_id.id,
                'team_id': check.point_id.team_id.id or self.env['quality.alert.team'].search([], limit=1).id,
                'name': _("Failure in: %s") % (check.title or check.display_name),
                'description': _("Quality check failed. Please investigate."),
            }
            alert_vals_list.append(alert_vals)

        if alert_vals_list:
            self.env['quality.alert'].create(alert_vals_list)

            
        for check in self:
            # Determine the parent document (either production or service request)
            parent_field = None
            parent_id = None
            if check.production_id:
                parent_field = 'production_id'
                parent_id = check.production_id.id
            elif check.service_request_id:
                parent_field = 'service_request_id'
                parent_id = check.service_request_id.id

            # If we have a parent and it's a FAT test, reset other checks
            if parent_field and check.fat_name in FAT_TEST_TYPE_TO_FIELD_MAP:
                
                domain_to_reset = [
                    (parent_field, '=', parent_id),
                    ('quality_state', '!=', 'none'),
                ]
                checks_to_reset = self.env['quality.check'].search(domain_to_reset)

                if checks_to_reset:
                    checks_to_reset.write({'quality_state': 'none'})
                    checks_to_reset._update_fat_instance_state('pending')
        return res
