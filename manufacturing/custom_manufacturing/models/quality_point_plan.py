from odoo import models, fields, api

FAT_TEST_TYPES_SELECTION = [
    ('fat_step1_insulation', 'FAT 1: Insulation Resistance'),
    ('fat_step2_ratio', 'FAT 2: Ratio Test'),
    ('fat_step3_no_load', 'FAT 3: NO Load Loss'),
    ('fat_step4_load_loss', 'FAT 4: Load Loss'),
    ('fat_step5_winding', 'FAT 5: Winding Resistance'),
    ('fat_step6_separate', 'FAT 6: Separate Source'),
    ('fat_step7_induced', 'FAT 7: Induced Overvoltage'),
]


class QualityTestPlan(models.Model):
    _name = 'quality.test.plan'
    _description = 'Quality Test Plan'

    name = fields.Char('Plan Name', required=True)
    active = fields.Boolean(default=True)
    product_ids = fields.Many2many('product.product', string='Products')
    picking_type_ids = fields.Many2many(
        'stock.picking.type', string='Operation Types')
    plan_line_ids = fields.One2many(
        'quality.test.plan.line', 'plan_id', string='Test Steps')
    


class QualityTestPlanLine(models.Model):
    _name = 'quality.test.plan.line'
    _description = 'Quality Test Plan Line'
    _order = 'sequence, id'

    plan_id = fields.Many2one(
        'quality.test.plan', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char('Step Name', required=True)
    team_id = fields.Many2one('quality.alert.team',
                              'Quality Team', required=True)
    test_type = fields.Selection(FAT_TEST_TYPES_SELECTION, required=True)
    note = fields.Html('Instructions')


class QualityPoint(models.Model):
    _inherit = 'quality.point'

    test_plan_id = fields.Many2one(
        'quality.test.plan', 'Test Plan')
    workorder_type_ids = fields.Many2many('workorder.type', string='Workorder Types')
    

    def _get_checks_values_from_plan(self, product, company):
        self.ensure_one()
        if not self.test_plan_id:
            return []

        return [{
            'name': line.name,
            'product_id': product.id,
            'point_id': self.id,
            'team_id': line.team_id.id,
            'company_id': company.id,
            'fat_name': line.test_type,
            'note': line.note,
        } for line in self.test_plan_id.plan_line_ids]