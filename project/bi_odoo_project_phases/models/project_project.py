# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################

from odoo import api, fields, models, _,tools


class ProjectPhase(models.Model):
    _name = 'project.task.phase'
    _description = 'Task Phase'
    _order = 'sequence'
    
    name = fields.Char(string='Phase Name')
    sequence = fields.Integer(string='Sequence')
    project_id = fields.Many2one('project.project',string='Project',default=lambda self: self.env.context.get('default_project_id'))
    start_date = fields.Date(string='Start Date', copy=False)
    end_date = fields.Date(string='End Date', copy=False)
    company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env['res.company']._company_default_get())
    user_id = fields.Many2one('res.users', string='Assignees', default=lambda self: self.env.uid)
    task_count = fields.Integer(compute="get_task",string='Count')
    notes = fields.Text(string='Notes')

    def action_project_phase_task(self):
        self.ensure_one()
        return {
            'name': 'Tasks',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'domain': [('phase_id', '=', self.id)],
        }

    def get_task(self):
        for rec in self:
            records = self.env['project.task'].search([('phase_id','=',rec.id)])
            rec.task_count = len(records)

class Task(models.Model):
    _inherit = 'project.task'    
    
    phase_id = fields.Many2one('project.task.phase', string='Project Phase')
    user_id = fields.Many2one('res.users', string='Assignee', default=lambda self: self.env.uid)
    
class ProjectProject(models.Model):
    _inherit='project.project'
    
    project_phase_count = fields.Integer('Job Note', compute='_get_project_phase_count')

    def _get_project_phase_count(self):
        for project_phase in self:
            project_phase_ids = self.env['project.task.phase'].search([('project_id','=',project_phase.id)])
            project_phase.project_phase_count = len(project_phase_ids)

    def action_project_phase(self):
        self.ensure_one()
        return {
            'name': 'Phases',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'project.task.phase',
            'domain': [('project_id', '=', self.id)],
        }
        

class ReportProjectTaskUser(models.Model):
    _inherit = "report.project.task.user"
    _description = "Tasks Analysis"

    phase_id = fields.Many2one('project.task.phase', string='Project Phase', readonly=True)

    def _select(self):
        return super(ReportProjectTaskUser, self)._select() + ', t.phase_id AS phase_id'

    


