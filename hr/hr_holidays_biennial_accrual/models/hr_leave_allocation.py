from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    @api.onchange('date_from', 'accrual_plan_id', 'employee_id')
    def _onchange_date_from(self):
        
        if self.accrual_plan_id and self.employee_id and self.date_from:
            biennial_level = self.accrual_plan_id.level_ids.filtered(lambda l: l.frequency == 'biennially')

            if biennial_level:
                _logger.info("Biennial increment plan detected. Running final historical summation with validity window.")
                
                level = biennial_level[0]
                start_date = self.date_from
                today = date.today()
                
                historical_grants = []
                
                if start_date < today:
                    current_years_of_service = relativedelta(today, start_date).years
                    
                    for year_offset in range(1, current_years_of_service + 1):
                        
                        days_granted_on_this_anniversary = year_offset // 2
                        
                        historical_grants.append(days_granted_on_this_anniversary)

                valid_grants_to_sum = []
                if level.accrual_validity:
                    if level.accrual_validity_type == 'year':
                        num_years_to_sum = level.accrual_validity_count
                    else: 
                        num_years_to_sum = level.accrual_validity_count // 12
                    
                    valid_grants_to_sum = historical_grants[-num_years_to_sum:]
                else:
                    valid_grants_to_sum = historical_grants

                total_accumulated_days = sum(valid_grants_to_sum)

                self.number_of_days = total_accumulated_days
                self.number_of_days_display = total_accumulated_days
                
                
                anniversary_this_year = start_date.replace(year=today.year)
                
                if anniversary_this_year < today:
                    self.nextcall = anniversary_this_year.replace(year=today.year + 1)
                else:
                    self.nextcall = anniversary_this_year
                
                self.lastcall = self.date_from

                return

        return super()._onchange_date_from()