from odoo import models, fields

class MrpProductionTemplate(models.Model):
    _name = 'mrp.production.template'
    _description = 'Manufacturing Process Template'

    name = fields.Char(required=True)
    production_type = fields.Selection([
        ('manufacturing', 'Manufacturing'),
        ('maintenance', 'Maintenance'),
        ('test', 'Test')
    ], default='manufacturing', required=True)
    # Changed from 'task_ids' to 'step_ids' to represent flat operations
    step_ids = fields.One2many('mrp.process.step', 'template_id', string='Steps')

class MrpProcessStep(models.Model):
    _name = 'mrp.process.step'
    _order = 'sequence, id'

    template_id = fields.Many2one('mrp.production.template')
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    workcenter_id = fields.Many2one('mrp.workcenter', required=True)
    output_product_id = fields.Many2one('product.product', string="Specific Output")
    
    # Dependency logic within the template
    blocked_by_step_ids = fields.Many2many(
        'mrp.process.step', 'mrp_step_rel', 'step_id', 'blocker_id',
        domain="[('template_id', '=', template_id), ('id', '!=', id)]"
    )