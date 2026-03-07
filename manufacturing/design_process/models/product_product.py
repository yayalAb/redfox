from odoo import models, fields

class ProductProdcut(models.Model):
    _inherit = 'product.product'

    lv_design = fields.One2many(related='product_tmpl_id.lv_design')
    hv_design = fields.One2many(related='product_tmpl_id.hv_design')

    def action_view_lv_design(self):
        self.ensure_one()

        return {
            'name': 'LV Designs',
            'type': 'ir.actions.act_window',
            'res_model': 'lv.winding.design',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                    'default_product_temp_id': self.product_tmpl_id.id,
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
                    'default_product_temp_id': self.product_tmpl_id.id,
            }
        }