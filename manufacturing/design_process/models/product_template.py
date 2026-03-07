from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    lv_design = fields.One2many('lv.winding.design', 'product_tmpl_id')
    hv_design = fields.One2many('hv.winding.design', 'product_tmpl_id')

    def action_view_lv_design(self):
        self.ensure_one()

        return {
            'name': 'LV Designs',
            'type': 'ir.actions.act_window',
            'res_model': 'lv.winding.design',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {
                    'default_product_tmpl_id': self.id,
            }
        }
    
    def action_view_hv_design(self):
        self.ensure_one()

        return {
            'name': 'HV Designs',
            'type': 'ir.actions.act_window',
            'res_model': 'hv.winding.design',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                    'default_product_tmpl_id': self.id,
            }
        }

