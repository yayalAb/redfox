from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
import logging
import re

_logger = logging.getLogger(__name__)
class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    @api.constrains('salary_expected', 'salary_proposed')
    def _check_positive_salary(self):
        for record in self:
            if record.salary_expected and record.salary_expected < 0:
                raise ValidationError('Expected salary must be a positive number.')
            if record.salary_proposed and record.salary_proposed < 0:
                raise ValidationError('Proposed salary must be a positive number.')

    @api.constrains('partner_phone')
    def _check_phone_format(self):
        eth_phone_regex = r'^(\+251|0)9[0-9]{8}$'
        for record in self:
            if record.partner_phone and not re.match(eth_phone_regex, record.partner_phone):
                raise ValidationError('Phone number must match Ethiopian format (e.g., +251912345678 or 0912345678).')



    """used to check if the person that clicked the create employee button has access to create it. (helps keep the same behaviour as the unmodified.)"""
    def _check_interviewer_access(self):
        if self.env.user.has_group('hr_recruitment.group_hr_recruitment_interviewer') and not self.env.user.has_group('hr_recruitment.group_hr_recruitment_user'):
            raise UserError(_('You are not allowed to perform this action.'))

    """modifying the action called when the button (create employee) is clicked in the applicant page."""
    def create_employee_from_applicant(self):
        self.ensure_one()
        self._check_interviewer_access()

        if not self.partner_id:
            if not self.partner_name:
                raise UserError(_('Please provide a candidate name before creating an employee.'))
            # Create the partner now.
            partner = self.env['res.partner'].create({
                'is_company': False,
                'name': self.partner_name,
                'email': self.email_from,
                'phone': self.partner_phone,
            })
            self.partner_id = partner.id
        
        # Prepare defaults from the applicant
        defaults = {
            'name': self.partner_name or self.partner_id.name,
            'job_id': self.job_id.id,
            'job_title': self.job_id.name,
            'department_id': self.department_id.id,
            'work_email': self.email_from,
            'work_phone': self.partner_phone,
            'applicant_id': self.id,
            # Explicitly tell the form which partner to use for BOTH roles
            'work_contact_id': self.partner_id.id,
            'address_home_id': self.partner_id.id,
        }

        #Prepare the action to open the form
        action = self.env.ref('hr.open_view_employee_list_my').read()[0]
        action.update({
            'view_mode': 'form',
            'views': [(self.env.ref('hr.view_employee_form').id, 'form')],
            'res_id': False,
        })

        # create the context by adding the needed default things
        ctx = self.env.context.copy()
        ctx.update({
            'default_%s' % k: v for k, v in defaults.items()
        })
        #this ensures that the save method called will be executed only when clicked from the 'create employee buton
        ctx['create_from_applicant_flow'] = True

        latest_offer = self.env['hr.contract.salary.offer'].search(
            [('applicant_id', '=', self.id)],
            order='id desc',
            limit=1
        )
        if latest_offer and latest_offer.contract_template_id:
            # Add the template ID to the context. This is the key change.
            ctx['contract_template_id_from_applicant'] = latest_offer.contract_template_id.id
            _logger.info(f"Passing contract template ID {latest_offer.contract_template_id.id} in context.")
            if latest_offer.contract_start_date:
                # Add the contract start date to the context
                ctx['contract_start_date_from_applicant'] = latest_offer.contract_start_date
                _logger.info(f"Passing contract start date {latest_offer.contract_start_date} in context.")
                
        action['context'] = ctx
        return action