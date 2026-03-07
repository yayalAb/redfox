# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class project_task(models.Model):
    _inherit = 'project.task'
    _rec_name = 'name'

    sequence_name = fields.Char("Sequence   ",copy=False)
    is_custom = fields.Boolean(string = "Custom ")

    @api.model_create_multi
    def create(self,vals_list):
        if self._context.get('default_is_custom'):
            for vals in vals_list:
                if vals.get('sequence_name', _('New')) == _('New'):
                    vals['sequence_name'] = self.env['ir.sequence'].next_by_code('project.tasks') or _('New')
        return super(project_task, self).create(vals_list)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
