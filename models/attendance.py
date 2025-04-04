from datetime import timedelta



from odoo import models, fields,api
import logging
from datetime import datetime, time, timedelta
import pytz
from .attendance_status import Status

# from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class Attendance(models.Model):
    _name = 'attendance_log'  # Name of the model
    _description = 'Attendance logging'  # Description of the model


    # Fields for the device name and serial number
    enroll_id = fields.Integer()
    my_datetime = fields.Datetime(string="time")
    event = fields.Integer()

    inherit_emp_obj = fields.Many2one('inherit_emp', string="Employee", store=True)
    employee_name = fields.Char(related='inherit_emp_obj.employee_id.name', string="Employee Name", store=True,readonly=True)



    def create_check_in_record(self, inherit_emp, utc_time,start_from):
        """Create a new check-in record for the employee."""
        hour = self._get_hour_minute(utc_time)
        print(f"time check in  for an employee :   {hour}")
        print(f"time shift for an employee : {start_from}")
        print(f"minimum time to make check in : {start_from-1}")
        print(f"maximum time to make check in : {start_from+3}")
        if hour>start_from+3:
            print("refuse to make check in")
            return False
        elif hour>=start_from-1 and hour<=start_from +3:
            hr_attendance = self.env['hr.attendance'].sudo().create({
                'employee_id': inherit_emp.employee_id.id,  # Employee ID
                'check_in': utc_time.strftime("%Y-%m-%d %H:%M:%S"),  # Check-in time (formatted)
                # 'check_out': False,  # No check-out time as it’s a check-in
                # 'worked_hours': 0.0,  # Initially no worked hours  # Optional: If you want to track the device used for check-in
            })
            print(
                f"Created check-in record for {inherit_emp.employee_id.name} at {utc_time.strftime('%Y-%m-%d %H:%M:%S')}")

            return hr_attendance






    # Create the check-in record for the employee

    def _get_hour(self, date):
        local_tz = pytz.timezone("Asia/Riyadh")  # Riyadh is UTC+3
        local_time = date.astimezone(local_tz)
        return local_time.hour

    def _get_hour_minute(self, date):
        local_tz = pytz.timezone("Asia/Baghdad")  # Change to Baghdad timezone if needed
        local_time = date.astimezone(local_tz)
        return round(local_time.hour + (local_time.minute / 60), 2)  # Return both hour and minute


    def _get_day_of_week(self, utc_time):
        """Return the day of the week based on Baghdad timezone (Sunday, Monday, etc.)."""
        local_tz = pytz.timezone("Asia/Baghdad")  # Convert UTC time to Baghdad timezone
        local_time = utc_time.astimezone(local_tz)
        return local_time.strftime("%A")  # Returns full day name (e.g., "Monday")



    # def has_existing_check_in_t(self, employee_id, utc_time,diff,start_from,end_to):
    #     """Check if employee has already checked in and has not checked out yet
    #        (considering today, yesterday, and last 24 hours)."""
    #
    #     # Calculate the start of yesterday and today
    #     start_of_yesterday = (utc_time - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
    #     start_of_today = utc_time.strftime("%Y-%m-%d 00:00:00")
    #
    #     hour = self._get_hour_minute(utc_time)
    #
    #     # Search for check-ins from yesterday or today that do not have a check-out yet
    #     existing_check_in = self.env['hr.attendance'].sudo().search([
    #         ('employee_id', '=', employee_id),
    #         '|',  # OR condition to check for both yesterday and today
    #         '|',
    #         ('check_in', '>=', start_of_yesterday),  # Check-in time from yesterday
    #         ('check_out', '=', False),  # No check-out yet
    #         '|',
    #         ('check_in', '>=', start_of_today),  # Check-in time from today
    #         ('check_out', '=', False),
    #         '|',
    #         ('check_in','>=',start_of_today),
    #         ('check_out', '!=', False),
    #         # No check-out yet
    #     ], limit=1)
    #
    #     # If no check-in without check-out found from yesterday or today
    #     if not existing_check_in:
    #         return Status.new_check_in
    #
    #     print(f"end shift by default : {end_to}")
    #     print(f"minimum end shift  : {end_to-3}")
    #     print(f"max shift  : {end_to+1}")
    #     print(f"time an employe may does check in or check out  : {hour}")
    #
    #     # If a check-in without check-out is found today or yesterday, check the worked hours
    #     last_shift = existing_check_in
    #     print(f"amount of houre should an employee works is : {diff}")
    #
    #     if  not hour>=end_to-3 or not hour<=end_to+1:
    #         print(f"you can not make check out any more")
    #         return Status.prevent
    #     if hour>=end_to-3 and hour<=end_to+1:
    #         print("system allows you to make check out")
    #         return Status.update_check_out
    def _get_date_next_day(self,utc_time):
        date_today = utc_time.date()
        next_day = date_today + timedelta(days=1)
        start_of_next_day = datetime.combine(next_day, datetime.min.time())
        formatted_next_day = start_of_next_day.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_next_day
        # This gives you just the date part (YYYY-MM-DD)

    def _get_date_prev_day(self,utc_time):
        date_today = utc_time.date()
        prev_day = date_today - timedelta(days=1)
        start_of_prev_day = datetime.combine(prev_day, datetime.min.time())
        formatted_prev = start_of_prev_day.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_prev
        # This gives you just the date part (YYYY-MM-DD)

    def _get_date_today_day(self, utc_time):
        date_today = utc_time.date()
        start_of_next_day = datetime.combine(date_today, datetime.min.time())
        formatted_today = start_of_next_day.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_today
        # This gives you just the date part (YYYY-MM-DD)

    def has_existing_check_in_t(self, employee_id, utc_time, diff, start_from, end_to):
        """Check if employee has already checked in and has not checked out yet (for a specific date)."""

        # Get the current date in year-month-day format
        date_today = utc_time.date()  # This gives you just the date part (YYYY-MM-DD)

        # Calculate start of today and yesterday for exact date comparison
        start_of_today = datetime.combine(date_today, datetime.min.time())
        formmat_today  = self._get_date_today_day(utc_time)

        # next_day = date_today + timedelta(days=1)
        # start_of_next_day = datetime.combine(next_day, datetime.min.time())
        # formatted_next_day = self._get_date_next_day(utc_time)


        # Option 2: Get the previous day's start (midnight)
        # previous_day = date_today - timedelta(days=1)
        # start_of_previous_day = datetime.combine(previous_day, datetime.min.time())

        # print(f"formmat next today :{formatted_next_day}")
        print(f"formmat today : {formmat_today}")

        # start_of_today = "2025-03-19 00:00:00"
        print(f"date today : {start_of_today}")

        hour = self._get_hour_minute(utc_time)

        # Search for check-ins and check-outs from today or yesterday for the given employee
        existing_check_in = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', start_of_today),  # Only check-ins from today
            ('check_in', '<', start_of_today + timedelta(days=1)),  # Ensures only today's records are checked
        ], limit=1)

        # If no check-in without check-out found from yesterday or today
        if not existing_check_in:
            return Status.new_check_in

        print(f"end shift by default : {end_to}")
        print(f"minimum end shift : {end_to - 3}")
        print(f"max shift : {end_to + 1}")
        print(f"time an employee may do check-in or check-out: {hour}")

        # If a check-in without check-out is found today or yesterday, check the worked hours
        last_shift = existing_check_in
        print(f"Amount of hours the employee should work: {diff}")

        if not (hour >= end_to - 3 and hour <= end_to + 1):
            print(f"You cannot check out anymore.")
            return Status.prevent
        if hour >= end_to - 3 and hour <= end_to + 1:
            print("System allows you to check out.")
            return Status.update_check_out

        # If worked hours are 8 or more, allow the creation of a new check-in
        # print(f"Employee {employee_id} has worked {last_shift.worked_hours} hours, allowing new check-in.")
        # return Status.new_check_in

    def create_attendance_logs(self, attendance_log_data):
        """Process and create attendance records, consider first entry as check-in, rest as check-out."""
        attendance_records = []
        hr_attendance_records = []
        errors = []
        today_day_number = str(datetime.today().weekday())

        print(f"day today : {today_day_number}")

        for data in attendance_log_data:
            enroll_id, sn_value, utc_time = data['enroll_id'], data['sn_value'], data['utc_time']

            inherit_emp = self.get_employee_by_fingerprint(enroll_id)
            if not inherit_emp:
                errors.append(f"No employee found for enroll_id: {enroll_id} and device serial_number: {sn_value}")
                continue

            print(f"day today : {today_day_number}")

            obj = inherit_emp.get_object_shift(today_day_number)
            if obj:
                print(f"start from : {obj.hour_from}")
                print(f"End to : {obj.hour_to}")
            else:
                print(f"object is an empty")

            e = self.has_existing_check_in_t(inherit_emp.employee_id.id, utc_time,self._get_work_hours(obj.hour_from,obj.hour_to),obj.hour_from,obj.hour_to)

            if e==Status.prevent:
                print("can not add record for check in or check out")

            elif e==Status.new_check_in:
                print(f"Creating a check-in for {inherit_emp.employee_id.name} as no check-in exists.")
                hr_attendance_records.append(self.create_check_in_record(inherit_emp, utc_time, obj.hour_from))

            elif e==Status.update_check_out:
                print(f"Updating check-out time for {inherit_emp.employee_id.name}.")
                self.update_check_out_time(inherit_emp.employee_id.id, utc_time)



            attendance_records.append(self.create_attendance_log_entry(enroll_id, utc_time, inherit_emp))

        # Bulk create logs after processing all the entries
        self.bulk_create_logs(attendance_records, hr_attendance_records)

    # def create_attendance_logs(self, attendance_log_data):
    #     """Process and create attendance records, consider first entry as check-in, rest as check-out."""
    #     attendance_records = []
    #     hr_attendance_records = []
    #     errors = []
    #     today_day_number = str(datetime.today().weekday())
    #     print(f"day today : {today_day_number}")
    #
    #
    #     for data in attendance_log_data:
    #         enroll_id, sn_value, utc_time = data['enroll_id'], data['sn_value'], data['utc_time']
    #
    #         inherit_emp = self.get_employee_by_fingerprint(enroll_id)
    #         if not inherit_emp:
    #             errors.append(f"No employee found for enroll_id: {enroll_id} and device serial_number: {sn_value}")
    #             continue
    #
    #         today_day_number = str(datetime.today().weekday())
    #         print(f"day today : {today_day_number}")
    #
    #         obj = inherit_emp.get_object_shift(today_day_number)
    #         if obj:
    #             print(f"start from : {obj.hour_from}")
    #             print(f"start from : {obj.hour_to}")
    #         else:
    #             print(f"object is an empty")
    #
    #
    #
    #
    #
    #
    #
    #         # Check if the employee already has a valid check-in for today or yesterday
    #         if self.has_existing_check_in(inherit_emp.employee_id.id, utc_time) is None:
    #             print(f"Creating a check-in for {inherit_emp.employee_id.name} as no check-in exists.")
    #             hr_attendance_records.append(self.create_check_in_record(inherit_emp, utc_time))
    #
    #
    #         elif not self.has_existing_check_in(inherit_emp.employee_id.id, utc_time):
    #             print(f"Updating check-out time for {inherit_emp.employee_id.name}.")
    #             self.update_check_out_time(inherit_emp.employee_id.id, utc_time)
    #
    #         else:
    #             print(f"Creating a check-in for {inherit_emp.employee_id.name} as no check-in exists.")
    #             hr_attendance_records.append(self.create_check_in_record(inherit_emp, utc_time))
    #         # Log the entry for attendance log (not hr.attendance)
    #         attendance_records.append(self.create_attendance_log_entry(enroll_id, utc_time, inherit_emp))
    #
    #     # Bulk create logs after processing all the entries
    #     self.bulk_create_logs(attendance_records, hr_attendance_records)



    def get_employee_by_fingerprint(self, enroll_id):
        """Retrieve employee record using fingerprint ID."""
        return self.env["inherit_emp"].sudo().search([('finger_print_id', '=', enroll_id)], limit=1)

    def has_completed_attendance(self, employee_id, utc_time):
        """Check if an employee has completed attendance for the day."""
        return bool(self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', utc_time.strftime("%Y-%m-%d 00:00:00")),
            ('check_in', '<=', utc_time.strftime("%Y-%m-%d 23:59:59")),
            ('check_out', '!=', False)
        ], limit=1))

    def _get_work_hours(self,check_in,check_out):
        return check_out-check_in



    # def has_existing_check_in(self, employee_id, utc_time, check_in_shift, check_in_attendance,hr_to):
    #     """Check if employee has already checked in and has not checked out yet
    #        (considering today, yesterday, and last 24 hours)."""
    #
    #     # Calculate the start of yesterday and today
    #     start_of_yesterday = (utc_time - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
    #     start_of_today = utc_time.strftime("%Y-%m-%d 00:00:00")
    #
    #     # Search for check-ins from yesterday or today that do not have a check-out yet
    #     existing_check_in = self.env['hr.attendance'].sudo().search([
    #         ('employee_id', '=', employee_id),
    #         '|',  # OR condition to check for both yesterday and today
    #         '|',
    #         ('check_in', '>=', start_of_yesterday),  # Check-in time from yesterday
    #         ('check_out', '=', False),  # No check-out yet
    #         '|',
    #         ('check_in', '>=', start_of_today),  # Check-in time from today
    #         ('check_out', '=', False),  # No check-out yet
    #     ], limit=1)
    #
    #     # If no check-in without check-out found from yesterday or today
    #     if not existing_check_in:
    #         return None
    #
    #
    #
    #     # If a check-in without check-out is found today or yesterday, check the worked hours
    #     last_shift = existing_check_in
    #     # if self._is_an_earily(last_shift.check_in,check_in_shift):
    #     #     print("you are early")
    #     print(f"check in an employee : {self._get_hour(existing_check_in.check_in)}")
    #     work_hour = 0
    #
    #     if  not check_in_shift or not check_in_attendance:
    #         print("you are new")
    #     else:
    #         employee_check_in = self._get_hour(existing_check_in.check_in)
    #         if self._is_an_earily(check_in_shift,employee_check_in):
    #             work_hour = self._get_work_hours(employee_check_in,hr_to)
    #             print(f"default hours should an employee work : {self._get_work_hours(employee_check_in,hr_to)}")
    #             print("you are early")
    #         else:
    #             work_hour = self._get_work_hours(employee_check_in, hr_to)
    #             print(f"default hours should an employee work : {self._get_work_hours(employee_check_in, hr_to)}")
    #             print("you are not early")
    #
    #
    #     if last_shift.worked_hours is not None :
    #         if last_shift.worked_hours < work_hour  :
    #             print(f"work hours for an employee :  {last_shift.worked_hours}")
    #             print(f"Employee {employee_id} has worked less than {work_hour} hours, not allowing new check-in.")
    #             return False
    #
    #         if last_shift.worked_hours >= work_hour and last_shift.worked_hours < work_hour+1 :
    #             print(f"Employee {employee_id} has worked more than {work_hour} hours")
    #             return True
    #
    #
    #         # if  last_shift.worked_hours < work_hour+1 :
    #         #     print("allow an employee to work 1 hour +++ ")
    #         #     return False
    #         #
    #         # if last_shift.worked_hours > work_hour+1:
    #         #     print("un acceptable adding check out for an employee who worked more thant required hours")
    #         #     return False
    #
    #     # If worked hours are 8 or more, allow the creation of a new check-in
    #     print(f"Employee {employee_id} has worked {last_shift.worked_hours} hours, allowing new check-in.")
    #     return True
    def has_existing_check_in(self, employee_id, utc_time):
        """Check if employee has already checked in and has not checked out yet
           (considering today, yesterday, and last 24 hours)."""

        # Calculate the start of yesterday and today
        start_of_yesterday = (utc_time - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
        start_of_today = utc_time.strftime("%Y-%m-%d 00:00:00")

        # Search for check-ins from yesterday or today that do not have a check-out yet
        existing_check_in = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee_id),
            '|',  # OR condition to check for both yesterday and today
            '|',
            ('check_in', '>=', start_of_yesterday),  # Check-in time from yesterday
            ('check_out', '=', False),  # No check-out yet
            '|',
            ('check_in', '>=', start_of_today),  # Check-in time from today
            ('check_out', '=', False),  # No check-out yet
        ], limit=1)

        # If no check-in without check-out found from yesterday or today
        if not existing_check_in:
            return None

        # If a check-in without check-out is found today or yesterday, check the worked hours
        last_shift = existing_check_in

        if last_shift.worked_hours is not None and last_shift.worked_hours < 8:
            # If the worked hours are less than 8, prevent creating a new check-in
            print(f"Employee {employee_id} has worked less than 8 hours, not allowing new check-in.")
            return False

        # If worked hours are 8 or more, allow the creation of a new check-in
        print(f"Employee {employee_id} has worked {last_shift.worked_hours} hours, allowing new check-in.")
        return True

    def update_check_out_time(self, employee_id, utc_time):
        """Update check-out time for an employee."""
        hr_attendance = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee_id),
            ('check_in', '<=', utc_time.strftime("%Y-%m-%d %H:%M:%S"))
        ], order='check_in desc', limit=1)

        if hr_attendance:
            hr_attendance.write({'check_out': utc_time.strftime("%Y-%m-%d %H:%M:%S")})
        else:
            print(f"No check-in record found for employee {employee_id} to update check-out.")

    def _is_an_earily(self, check_in_shift, check_in_attendacne):
        # hour_employee : from odoo check -in
        # hour_device : from check_in shift

        return True if check_in_attendacne < check_in_shift else False
    def bulk_create_logs(self, attendance_records, hr_attendance_records):
        """Bulk insert attendance log and check-in records."""
        if attendance_records:
            self.env['attendance_log'].sudo().create(attendance_records)
        if hr_attendance_records:
            self.env['hr.attendance'].sudo().create(hr_attendance_records)

    def create_attendance_log_entry(self, enroll_id, utc_time, inherit_emp,hour_device='',hour_employee=''):
        # we will discuss that tomorrow by permission allah///
        # condition employee _ has come earlier
        """Prepare an attendance log entry for bulk creation."""
        return {
            'enroll_id': enroll_id,
            'my_datetime': utc_time.strftime("%Y-%m-%d %H:%M:%S"),
            'inherit_emp_obj': inherit_emp.id
        }



    def _get_all_active_ids(self):
        return self.env.context.get('active_ids',[])
    # this function get all record from db by active_ids
    def _get_all_records_by_active_ids(self):
        active_ids = self._get_all_active_ids()  # Get active_ids
        return self.browse(active_ids)

    def handel_time_zone(self,time):
        local_time = time + timedelta(hours=3)
        time_str = local_time.strftime('%Y-%m-%d %I:%M:%S %p')
        return time_str



    # def _handle_yesterdays_unprocessed_records(self):
    #     """Check for unprocessed records from yesterday and set check-out time to 5 PM."""
    #     try:
    #         # Get current time and adjust for local time zone
    #         now_local = datetime.now() + timedelta(hours=3)  # Baghdad Time - GMT+3
    #         yesterday_local = now_local - timedelta(days=1)
    #
    #         # Convert to start and end of yesterday in Baghdad time
    #         start_of_yesterday = yesterday_local.replace(hour=0, minute=0, second=0, microsecond=0)
    #         end_of_yesterday = yesterday_local.replace(hour=23, minute=59, second=59, microsecond=999999)
    #
    #         # Build the SQL query to set check-out time to 5 PM for unprocessed records
    #         query = f"""
    #         UPDATE hr_attendance
    #         SET check_out =
    #             CASE
    #                 WHEN check_out IS NULL THEN '{start_of_yesterday.replace(hour=17, minute=0)}'  -- Default check-out time at 5 PM
    #                 ELSE check_out
    #             END
    #         WHERE check_in >= '{start_of_yesterday}'
    #           AND check_in <= '{end_of_yesterday}'
    #           AND check_out IS NULL;
    #         """
    #
    #         # Execute the query
    #         self.env.cr.execute(query)
    #
    #         print("Unprocessed records for yesterday have been handled. Check-out time set to 5 PM.")
    #
    #     except Exception as e:
    #         # Log any exceptions that occur during the process
    #         print(f"Error while handling unprocessed records: {str(e)}")
    #



