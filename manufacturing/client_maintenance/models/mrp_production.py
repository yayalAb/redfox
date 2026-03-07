from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    lv_design = fields.Many2one('lv.winding.design')    
    hv_design = fields.Many2one('hv.winding.design')
    service_request = fields.Many2one('service.request', string='Service Request')

    @api.model
    def create(self, vals):
        if vals.get('name', 'NEW') == 'NEW':
            if vals.get('is_nested') and vals.get('main_production'):
                parent_mo = self.browse(vals.get('main_production'))
                
                seq_num = vals.get('sequence', 0)
                
                vals['name'] = f"{parent_mo.name or 'New'}-SUB-{seq_num}"

            elif vals.get('production_type') == 'maintenance':
                vals['name'] = self.env['ir.sequence'].next_by_code('client.maintenance') or 'NEW'
            elif vals.get('production_type') == 'test':
                vals['name'] = self.env['ir.sequence'].next_by_code('client.test') or 'NEW'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('manufacturing.order') or 'NEW'

        return super(MrpProduction, self).create(vals)
  