# custom_quality_fat_plan/models/fat_test_models.py
from odoo import models, fields, api


class FatTestBase(models.AbstractModel):
    _name = 'fat.test.base'
    _description = 'Base Model for all FAT Test Steps'

    check_id = fields.Many2one(
        'quality.check', string='Quality Check', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='check_id.company_id')
    state = fields.Selection([
        ('pending', 'Pending'), ('failed', 'Failed'), ('passed', 'Passed'), ('approved', 'Approved')
    ], default='pending')


class FatStep1Insulation(models.Model):
    _name = 'fat.step1.insulation'
    _inherit = 'fat.test.base'
    _description = 'FAT Step 1: Insulation Resistance'

    hv_to_lv_earth = fields.Float('HV to LV + Earth (GΩ)')
    hv_to_g_earth = fields.Float('H.V to G + Earth (GΩ)')
    lv_to_g_earth = fields.Float('L.V to G + Earth (GΩ)')


class FatStep2Ratio(models.Model):
    _name = 'fat.step2.ratio'
    _inherit = 'fat.test.base'
    _description = 'FAT Step 2: Ratio Test'
    
    uv_un_tap1 = fields.Float('UV-un: Tap 1')
    uv_un_tap2 = fields.Float('UV-un: Tap 2')
    uv_un_tap3 = fields.Float('UV-un: Tap 3')
    uv_un_tap4 = fields.Float('UV-un: Tap 4')
    uv_un_tap5 = fields.Float('UV-un: Tap 5')
    vw_vn_tap1 = fields.Float('VW-vn: Tap 1')
    vw_vn_tap2 = fields.Float('VW-vn: Tap 2')
    vw_vn_tap3 = fields.Float('VW-vn: Tap 3')
    vw_vn_tap4 = fields.Float('VW-vn: Tap 4')
    vw_vn_tap5 = fields.Float('VW-vn: Tap 5')
    uw_wn_tap1 = fields.Float('UW-wn: Tap 1')
    uw_wn_tap2 = fields.Float('UW-wn: Tap 2')
    uw_wn_tap3 = fields.Float('UW-wn: Tap 3')
    uw_wn_tap4 = fields.Float('UW-wn: Tap 4')
    uw_wn_tap5 = fields.Float('UW-wn: Tap 5')


class FatStep3NoLoad(models.Model):
    _name = 'fat.step3.no.load'
    _inherit = 'fat.test.base'
    _description = 'FAT Step 3: NO Load Loss'
    u_rated_voltage = fields.Float('Phase U: Rated Voltage (V)')
    u_rated_current = fields.Float('Phase U: Rated Current (A)')
    u_losses = fields.Float('Phase U: Losses (W)')
    v_rated_voltage = fields.Float('Phase V: Rated Voltage (V)')
    v_rated_current = fields.Float('Phase V: Rated Current (A)')
    v_losses = fields.Float('Phase V: Losses (W)')
    w_rated_voltage = fields.Float('Phase W: Rated Voltage (V)')
    w_rated_current = fields.Float('Phase W: Rated Current (A)')
    w_losses = fields.Float('Phase W: Losses (W)')
    avg_rated_voltage = fields.Float('Avg: Rated Voltage (V)', compute='_compute_average')
    avg_rated_current = fields.Float('Avg: Rated Current (A)', compute='_compute_average')
    avg_losses = fields.Float('Avg: Losses (W)', compute='_compute_average')
    percent_no_load_current = fields.Float('% No Load Current')

    @api.depends('u_rated_voltage', 'u_rated_current', 'u_losses', 'v_rated_voltage', 'v_rated_current', 'v_losses', 'w_rated_voltage', 'w_rated_current', 'w_losses')
    def _compute_average(self):
        for rec in self:
            rec.avg_rated_voltage = (rec.u_rated_voltage + rec.v_rated_voltage + rec.w_rated_voltage) / 3
            rec.avg_rated_current = (rec.u_rated_current + rec.v_rated_current + rec.w_rated_current) / 3
            rec.avg_losses = (rec.u_losses + rec.v_losses + rec.w_losses) / 3


class FatStep4LoadLoss(models.Model):
    _name = 'fat.step4.load.loss'
    _inherit = 'fat.test.base'
    _description = 'FAT Step 4: Load Loss'
    u_rated_voltage = fields.Float('Phase U: Rated Voltage (V)')
    u_rated_current = fields.Float('Phase U: Rated Current (A)')
    u_losses = fields.Float('Phase U: Losses (W)')
    v_rated_voltage = fields.Float('Phase V: Rated Voltage (V)')
    v_rated_current = fields.Float('Phase V: Rated Current (A)')
    v_losses = fields.Float('Phase V: Losses (W)')
    w_rated_voltage = fields.Float('Phase W: Rated Voltage (V)')
    w_rated_current = fields.Float('Phase W: Rated Current (A)')
    w_losses = fields.Float('Phase W: Losses (W)')
    avg_rated_voltage = fields.Float('Avg: Rated Voltage (V)', compute='_compute_average')
    avg_rated_current = fields.Float('Avg: Rated Current (A)', compute='_compute_average')
    avg_losses = fields.Float('Avg: Losses (W)', compute='_compute_average')
    percent_impedance = fields.Float('% Impedance')

    @api.depends('u_rated_voltage', 'u_rated_current', 'u_losses', 'v_rated_voltage', 'v_rated_current', 'v_losses', 'w_rated_voltage', 'w_rated_current', 'w_losses')
    def _compute_average(self):
        for rec in self:
            rec.avg_rated_voltage = (rec.u_rated_voltage + rec.v_rated_voltage + rec.w_rated_voltage) / 3
            rec.avg_rated_current = (rec.u_rated_current + rec.v_rated_current + rec.w_rated_current) / 3
            rec.avg_losses = (rec.u_losses + rec.v_losses + rec.w_losses) / 3


class FatStep5Winding(models.Model):
    _name = 'fat.step5.winding'
    _inherit = 'fat.test.base'
    _description = 'FAT Step 5: Winding Resistance'
    amb_temp = fields.Float('Amb. Temp')
    tap_no = fields.Integer('Tap No')
    hv_uv = fields.Float('HV (Ω): UV')
    hv_vw = fields.Float('HV (Ω): VW')
    hv_uw = fields.Float('HV (Ω): UW')
    hv_avg = fields.Float('HV (Ω): AVG', compute='_compute_average')
    lv_uv = fields.Float('LV (mΩ): uv')
    lv_vw = fields.Float('LV (mΩ): vw')
    lv_uw = fields.Float('LV (mΩ): uw')
    lv_avg = fields.Float('LV (mΩ): AVG', compute='_compute_average')

    @api.depends('hv_uv', 'hv_uw', 'hv_uw', 'lv_uv', 'lv_vw', 'lv_uw')
    def _compute_average(self):
        for rec in self:
            rec.hv_avg = (rec.hv_uv + rec.hv_vw + rec.hv_uw) / 3
            rec.lv_avg = (rec.lv_uv + rec.lv_vw + rec.lv_uw) / 3


class FatStep6Separate(models.Model):
    _name = 'fat.step6.separate'
    _inherit = 'fat.test.base'
    _description = 'FAT Step 6: Separate Source'
    test1_applied_voltage = fields.Float(
        'Test 1 (B/n HV & LV): Applied Voltage (KV)')
    test1_duration = fields.Float('Test 1 Duration (Sec)')
    test1_remark = fields.Char('Test 1 Remark')
    test2_applied_voltage = fields.Float(
        'Test 2 (B/n LV & HV): Applied Voltage (KV)')
    test2_duration = fields.Float('Test 2 Duration (Sec)')
    test2_remark = fields.Char('Test 2 Remark')


class FatStep7Induced(models.Model):
    _name = 'fat.step7.induced'
    _inherit = 'fat.test.base'
    _description = 'FAT Step 7: Induced Overvoltage'
    applied_voltage = fields.Float('Applied Voltage (V)')
    applied_frequency = fields.Float('Applied Frequency (Hz)')
    duration = fields.Float('Duration (Sec)')
    remark = fields.Char('Remark')
