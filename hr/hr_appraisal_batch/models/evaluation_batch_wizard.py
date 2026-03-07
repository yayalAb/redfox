# evaluation_batch_wizard.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EvaluationBatchWizard(models.TransientModel):
    _name = 'evaluation.batch.wizard'
    _description = 'Generate Employee Evaluations in Batch'

    department_id = fields.Many2one('hr.department', string='Department')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    job_id = fields.Many2one('hr.job', string='Job Position')

    @api.onchange('department_id', 'job_id')
    def _onchange_employee_ids(self):
        """
        Dynamically populates the employee_ids field based on the selected
        department and/or job position.
        """
        domain = []
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        if self.job_id:
            domain.append(('job_id', '=', self.job_id.id))
        
        # If a domain is specified, find employees matching it.
        # Otherwise, clear the list.
        if domain:
            employees = self.env['hr.employee'].search(domain)
            self.employee_ids = [(6, 0, employees.ids)]
        else:
            self.employee_ids = [(5, 0, 0)] # Clear the list if no filters

    def generate_employee_evaluations(self):
        """
        Creates employee.evaluation records for each selected employee.
        """
        # Get the batch record from which this wizard was launched
        batch_id = self.env.context.get('active_id')
        if not batch_id:
            raise UserError(_("Could not find the batch record. Please try again."))
            
        batch = self.env['evaluation.batch'].browse(batch_id)
        
        if not self.employee_ids:
            raise UserError(_("You must select at least one employee to generate evaluations."))

        created_evals = self.env['employee.evaluation']
        skipped_employees = []

        for employee in self.employee_ids:
            # Check if an evaluation for this employee and period already exists
            existing_eval = self.env['employee.evaluation'].search([
                ('employee_id', '=', employee.id),
                ('period_id', '=', batch.period_id.id)
            ], limit=1)

            if existing_eval:
                skipped_employees.append(employee.name)
                continue # Skip to the next employee

            # Prepare values for the new evaluation
            vals = {
                'employee_id': employee.id,
                'batch_id': batch.id,
                'period_id': batch.period_id.id,
                'period_type': batch.period_type,
                # The onchange on employee_id in employee.evaluation will trigger 
                # to populate KPIs automatically.
            }
            created_evals |= self.env['employee.evaluation'].create(vals)
        
        # Link newly created evaluations to the batch record
        if created_evals:
            batch.write({'evaluation_line_ids': [(4, eval_id) for eval_id in created_evals.ids]})

        # Optional: Display a message if some evaluations were skipped
        if skipped_employees:
            message = _(
                "Evaluations were successfully generated. However, evaluations for the following "
                "employees were skipped because they already exist for this period: \n\n- %s"
            ) % ('\n- '.join(skipped_employees))
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Partial Generation'),
                    'message': message,
                    'sticky': True, # Keep the message until the user dismisses it
                    'type': 'warning',
                }
            }
            
        return {'type': 'ir.actions.act_window_close'}