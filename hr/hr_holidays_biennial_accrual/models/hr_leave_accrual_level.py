from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


DAYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
DAY_SELECT_VALUES = [str(i) for i in range(1, 29)] + ['last']
DAY_SELECT_SELECTION_NO_LAST = tuple(zip(DAY_SELECT_VALUES, (str(i) for i in range(1, 29))))

class AccrualPlanLevel(models.Model):
    _inherit = "hr.leave.accrual.level"

    frequency = fields.Selection(
        selection_add=[('biennially', 'Every 2 years')],
        ondelete={'biennially': 'cascade'}
    )

    _sql_constraints = [
        ('check_dates',
         "CHECK( (frequency IN ('daily', 'hourly')) or"
         "(week_day IS NOT NULL AND frequency = 'weekly') or "
         "(first_day > 0 AND second_day > first_day AND first_day <= 31 AND second_day <= 31 AND frequency = 'bimonthly') or "
         "(first_day > 0 AND first_day <= 31 AND frequency = 'monthly')or "
         "(first_month_day > 0 AND first_month_day <= 31 AND second_month_day > 0 AND second_month_day <= 31 AND frequency = 'biyearly') or "
         "(yearly_day > 0 AND yearly_day <= 31 AND frequency IN ('yearly', 'biennially')))",
         "The dates you've set up aren't correct. Please check them."),
        ('start_count_check', "CHECK( start_count >= 0 )", "You can not start an accrual in the past."),
        ('added_value_greater_than_zero', 'CHECK(added_value > 0)', "You must give a rate greater than 0 in accrual plan levels."),
        (
            'valid_yearly_cap_value',
            'CHECK(cap_accrued_time_yearly IS NOT TRUE OR COALESCE(maximum_leave_yearly, 0) > 0)',
            "You cannot have a cap on yearly accrued time without setting a maximum amount."
        ),
    ]

    def _get_next_date(self, last_call):
        next_date = super()._get_next_date(last_call)
        if self.frequency == 'biennially':
            month = MONTHS.index(self.yearly_month) + 1
            date = last_call + relativedelta(month=month, day=self.yearly_day)
            if last_call < date:
                return date
            else:
                return last_call + relativedelta(years=2, month=month, day=self.yearly_day)
        return next_date

    def _get_previous_date(self, last_call):
        previous_date = super()._get_previous_date(last_call)
        if self.frequency == 'biennially':
            month = MONTHS.index(self.yearly_month) + 1
            year_date = last_call + relativedelta(month=month, day=self.yearly_day)
            if last_call >= year_date:
                return year_date
            else:
                return last_call + relativedelta(years=-2, month=month, day=self.yearly_day)
        return previous_date