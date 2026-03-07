from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round, cache
from datetime import datetime, timedelta
from odoo import models, api, exceptions
class CustomHrContract(models.Model):
    _inherit = 'hr.contract'

    is_attendance_based = fields.Boolean(string='Is Attendance Based ?', default=False)



class custom_hr_attendance(models.Model):
    _inherit = 'hr.attendance'
    expected_working_hour=fields.Float(string="Expected Working Hours", compute='compute_expected_working_hours')
    overtime=fields.Float(string="Overtime", compute='compute_overtime_time_hours')
    is_less_then_one=fields.Boolean(string="Is less then 1 hour", compute='compute_overtime_time_hours')
    overtime_type_id = fields.Many2one('overtime.rate', string="Overtime type",tracking=True,)
    status = fields.Selection([
        ('draft', 'draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], 'Status', default='draft')


    # @api.model
    # def read(self, fields=None, load='_classic_read'):
    #     machines= self.env['zk.machine'].search([])
    #     try:
    #         for m in machines:
    #             m.download_attendance()
    #     except exceptions.AccessError as e:
    #         pass
    #     result = super(custom_hr_attendance, self).read(fields=fields, load=load)
    #     return result


    def approve_attendance_ot(self):
        for rec in self:
            if  not rec.overtime_type_id:
                raise  ValidationError("please select overtime type")

            rec.status='approved'
            ex_ot=self.env['overtime.calculator'].search([('overtime_type_id','=', rec.overtime_type_id.id),('employee_id','=',rec.employee_id.id),('state','in',['draft','submit'])], limit=1)
            if ex_ot:
                ex_ot.write({
                    'hours':ex_ot.hours + rec.overtime
                })

            else:
                self.env['overtime.calculator'].create({
                    'requested_by': self.env.user.employee_id.id,
                    'employee_id': rec.employee_id.id,
                    'start_date': rec.check_in,
                    'end_date': rec.check_out,
                    'overtime_type_id': rec.overtime_type_id.id,
                    'hours': rec.overtime
                })



    def rejected_attendance_ot(self):
        for rec in self:
            rec.status='rejected'

    def compute_expected_working_hours(self):
        for rec in self:
            if rec.employee_id.contract_id:
                schedules = rec.employee_id.contract_id.resource_calendar_id.attendance_ids
                total=0
                for schedule in schedules:
                    if schedule.dayofweek==self.return_index_of_day(rec.check_in.strftime("%A")):
                        duration =   schedule.hour_to - schedule.hour_from
                        total+=duration
                rec.expected_working_hour =total

            else:
                rec.expected_working_hour=0



    def compute_overtime_time_hours(self):
        for rec in self:
            if rec.worked_hours>rec.expected_working_hour:
                rec.overtime=rec.worked_hours-rec.expected_working_hour
                rec.is_less_then_one = False
                if rec.overtime >= 1:
                    rec.is_less_then_one=True
            else:
                rec.is_less_then_one = False
                rec.overtime=0


    def compute_worked_hours(self, employee_id, start_date, end_end):
        worked_days=0
        attendances=self.env['hr.attendance'].search([('check_in','>=',start_date),('check_out','<=',end_end),('employee_id', '=', employee_id.id)])
        for attendance in attendances:
            duration= attendance.check_out - attendance.check_in
            hours=(duration.total_seconds() / 3600)
            worked_days+=hours
        return  worked_days

    def compute_worked_days(self, employee_id, start_date, end_date,work_hour):
        # Get the total worked hours for the employee within the given date range
        # self.env.cr.execute('''
        #     SELECT SUM(EXTRACT(EPOCH FROM (check_out - check_in))/3600) AS total_hours
        #     FROM hr_attendance
        #     WHERE employee_id = %s AND check_in >= %s AND check_out <= %s
        # ''', (employee_id.id, start_date, end_date))
        attendance = self.env['hr.attendance'].search([('check_in', '>=', start_date), ('check_out', '<=', end_date), ('employee_id', '=', employee_id.id)])
        total_worked_hours=0
        for att in attendance:
            if att.overtime==0:
                total_worked_hours+=att.worked_hours
            elif att.expected_working_hour >0 and att.overtime>0 :
                total_worked_hours += att.expected_working_hour
        total_hours = total_worked_hours
        leaves = self.env['hr.leave'].search(
            [('date_from', '>=', start_date), ('date_to', '<=', end_date), ('employee_id', '=', employee_id.id),
             ('state', '=', "validate"), ('holiday_status_id.work_entry_type_id.name', 'not ilike', "Unpaid")])
        total_leave_days=0
        for leave in leaves:
            total_leave_days+=leave.number_of_days
        worked_days = total_leave_days + float_round(total_hours/work_hour, precision_digits=2)
        return worked_days

    def calculate_working_days(self, start_date, end_date, calender_id):
        daily_hours=self.fetch_daily_hours(calender_id.id)
        max_day = max(daily_hours, key=daily_hours.get)
        max_daily_hours = daily_hours[max_day]
        total_working_hours = 0
        # Iterate through each day in the date range
        current_date = start_date
        while current_date <= end_date:
            day_name = current_date.strftime("%A")
            if day_name in daily_hours:
                total_working_hours += daily_hours[day_name]
            current_date += timedelta(days=1)
        # Convert total working hours to working days
        working_days = total_working_hours / max_daily_hours  # 8 hours per day
        holidays=self.env['resource.calendar.leaves'].search([('date_from','>=',start_date),('date_to','<=',end_date)])
        working_days=working_days-len(holidays)
        return working_days, max_daily_hours

    def fetch_daily_hours(self, calendar_id):
        # Dictionary to map dayofweek to day names
        day_map = {
            '0': "Monday",
            '1': "Tuesday",
            '2': "Wednesday",
            '3': "Thursday",
            '4': "Friday",
            '5': "Saturday",
            '6': "Sunday"
        }

        # Initialize an empty dictionary to hold daily hours
        daily_hours = {}

        # SQL query to fetch daily hours based on the calendar_id
        self.env.cr.execute('''
            SELECT dayofweek, SUM(hour_to - hour_from) AS total_hours
            FROM resource_calendar_attendance
            WHERE calendar_id = %s
            GROUP BY dayofweek
            ORDER BY dayofweek
        ''', (calendar_id,))

        results = self.env.cr.fetchall()

        # Populate the dictionary with the results
        for dayofweek, total_hours in results:
            day_name = day_map[str(dayofweek)]
            daily_hours[day_name] = total_hours

        # Fill in the days that might not have entries (e.g., Sunday)
        for i in range(7):
            day_name = day_map[str(i)]
            if day_name not in daily_hours:
                daily_hours[day_name] = 0

        return daily_hours

    def return_index_of_day(self, str_name):

        if str_name== "Monday":
            return  '0'
        elif str_name== "Tuesday":
            return  '1'
        elif str_name== "Wednesday":
            return  '2'
        elif str_name== "Thursday":
            return  '3'
        elif str_name== "Friday":
            return  '4'
        elif str_name== "Saturday":
            return  '5'
        else:
            return  '6'




