from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    template_id = fields.Many2one(
        'mrp.production.template', string='Manufacturing Template')
    nested_orders = fields.One2many(
        'mrp.production', 'main_production', string='Nested Manufacturing Orders')
    main_production = fields.Many2one(
        'mrp.production', string='Parent Manufacturing Order')
    is_main = fields.Boolean(default=True, string='Is Main MO')
    is_nested = fields.Boolean(default=False, string='Is Nested MO')
    blocked_by_ids = fields.Many2many(
        'mrp.production', 'mrp_production_dependency_rel', 'mo_id', 'blocker_id',
        string='Blocked By', help="MOs that must be done before this one can start."
    )
    is_ready = fields.Boolean(compute="_compute_mrp_ready", store=True)
    sequence = fields.Integer(string='Nested Sequence', default=0, readonly=True)
    
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center')

    production_type = fields.Selection([
        ('manufacturing', 'Manufacturing'),
        ('maintenance', 'Maintenance'),
        ('test', 'Test')
    ], default='manufacturing', string='Production Type')

    production_started = fields.Boolean(
        string="Production Started", default=False, copy=False)

    def action_confirm(self):
        # Auto-assign template based on production type if not already set
        for mo in self:
            if not mo.template_id and mo.production_type == 'manufacturing':
                mo.template_id = self.env['mrp.production.template'].search([
                    ('production_type', '=', mo.production_type)
                ], limit=1)

        res = super(MrpProduction, self).action_confirm()

        for mo in self:
            # Only generate if Main MO, has template, and is New Manufacturing
            if mo.template_id and mo.is_main and mo.production_type == 'manufacturing':
                # Prevent duplicates
                if not mo.nested_orders:
                    mo._generate_nested_mos_from_template()
        return res

    def _generate_nested_mos_from_template(self):
        self.ensure_one()
        step_to_mo_map = {}
        
        steps = self.template_id.step_ids.sorted(key=lambda r: r.sequence)

        for step in steps:
            target_product = step.output_product_id or self.product_id
            
            mo_vals = {
                'product_id': target_product.id,
                'product_qty': self.product_qty,
                'product_uom_id': target_product.uom_id.id,
                'main_production': self.id,
                'production_type': self.production_type,
                
                # Hierarchy Flags
                'is_main': False,
                'is_nested': True,
                'company_id': self.company_id.id,
                'origin': f"{self.name} - {step.name}",
                'workcenter_id': step.workcenter_id.id,
            }

            new_mo = self.env['mrp.production'].create(mo_vals)
            step_to_mo_map[step.id] = new_mo
            new_mo.action_confirm()

        for step in steps:
            if step.blocked_by_step_ids:
                current_mo = step_to_mo_map[step.id]
                blocker_mos = []
                
                for dep_step in step.blocked_by_step_ids:
                    if dep_step.id in step_to_mo_map:
                        blocker_mos.append(step_to_mo_map[dep_step.id].id)
                
                if blocker_mos:
                    current_mo.write({'blocked_by_ids': [(6, 0, blocker_mos)]})


    @api.depends('state', 'blocked_by_ids', 'blocked_by_ids.state')
    def _compute_mrp_ready(self):
        for mo in self:
            mo.is_ready = not any(
                dep.state != 'done' for dep in mo.blocked_by_ids)


    def action_start(self):
        for mo in self:
            if not mo.is_ready:
                blockers = mo.blocked_by_ids.filtered(
                    lambda b: b.state != 'done')
                raise UserError(_("Wait for: %s") % ", ".join(
                    blockers.mapped('origin') or blockers.mapped('name')))

            if mo.components_availability_state != 'available':
                pass 

        res = super(MrpProduction, self).action_start()
        
        # 4. Set Custom Flag
        self.write({'production_started': True})
        return res

    @api.depends('production_started')
    def _compute_state(self):
        super(MrpProduction, self)._compute_state()
        for production in self:
            if production.state == 'progress' and not production.production_started:
                production.state = 'confirmed'

    def action_open_nested_mo(self):
        self.ensure_one()
        return {
            'name': 'Nested Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('main_production', '=', self.id)]
        }