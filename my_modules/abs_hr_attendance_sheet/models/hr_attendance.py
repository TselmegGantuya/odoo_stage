# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from odoo import api, fields, models, _
from datetime import datetime
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import time
import calendar
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    work_schedule = fields.Many2one('resource.calendar.attendance',string='Work Schedule', compute='_compute_work_schedule', readonly=True)

    def _compute_work_schedule(self):
        for attendance in self:
            allow_check_in_window_min = attendance.employee_id.company_id.allow_check_in_window * 60
            if attendance.check_in:
                dayofweek = False
                check_in_date = datetime.strptime(str(attendance.check_in), '%Y-%m-%d %H:%M:%S')
                attendance_day = calendar.day_name[check_in_date.weekday()]
                if attendance_day == 'Monday':
                    dayofweek = 0
                elif attendance_day == 'Tuesday':
                    dayofweek = 1
                elif attendance_day == 'Wednesday':
                    dayofweek = 2
                elif attendance_day == 'Thursday':
                    dayofweek = 3
                elif attendance_day == 'Friday':
                    dayofweek = 4
                elif attendance_day == 'Saturday':
                    dayofweek = 5
                elif attendance_day == 'Sunday':
                    dayofweek = 6
                if attendance_day:
                    if attendance.employee_id.resource_calendar_id:
                        work_schedule = self.env['resource.calendar.attendance'].sudo().search([('calendar_id', '=',  attendance.employee_id.resource_calendar_id.id),('dayofweek', '=', str(dayofweek))])
                        if work_schedule:
                            for work in work_schedule:
                                user_tz = self.env.user.tz or pytz.utc
                                local = pytz.timezone(user_tz)
                                check_in_time_date = datetime.strftime(pytz.utc.localize(datetime.strptime(str(attendance.check_in), DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")
                                check_in_time = datetime.strptime(str(check_in_time_date), '%Y-%m-%d %H:%M:%S')
                                since = datetime(check_in_date.year, check_in_date.month, check_in_date.day, 0, 0, 0 )
                                check_in_diff_seconds = (check_in_time-since).total_seconds()
                                actual_sign_in_minutes = (check_in_diff_seconds / 60)
                                planned_start_hour = work.hour_from
                                planned_start_minutes = planned_start_hour * 60
                                planned_end_hour = work.hour_to
                                planned_end_minutes = planned_end_hour * 60
                                if planned_start_minutes <= (actual_sign_in_minutes + allow_check_in_window_min) <= planned_end_minutes:
                                    attendance.work_schedule = work.id


class EmployeeAttendaceSheetDetail(models.Model):
    _name = "employee.attendace.sheet.detail"
    _order = 'date'

    employee_attendace_sheet_id = fields.Many2one('employee.attendace.sheet',string="Employee Attendace Sheet")
    date = fields.Date(string="Date")
    day = fields.Char(string="Day")
    planned_sign_in = fields.Char(string="Planned Sign In")
    planned_sign_out = fields.Char(string="Planned Sign Out")
    actual_sign_in = fields.Char(string="Actual Sign In")
    actual_sign_out = fields.Char(string="Actual Sign Out")
    late_in = fields.Char(string="Late In")
    overtime = fields.Char(string="Overtime")
    early_leave = fields.Char(string="Early Leave")


class EmployeeAttendaceSheet(models.Model):
    _name = "employee.attendace.sheet"

    name = fields.Char(string="Name")
    employee_id = fields.Many2one('hr.employee',string="Employee")
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    sheet_detail_ids = fields.One2many('employee.attendace.sheet.detail','employee_attendace_sheet_id',string="Sheet Detail")
    total_late_in = fields.Char(string="Total Late In", compute='_compute_total_time')
    total_number_of_late_in = fields.Integer(string="Total Number of Late In", compute='_compute_total_time')
    total_overtime = fields.Char(string="Total Overtime", compute='_compute_total_time')
    total_number_of_overtime = fields.Integer(string="Total Number of Overtime", compute='_compute_total_time')
    total_early_leave = fields.Char(string="Total Early Leave", compute='_compute_total_time')
    total_number_of_early_leave = fields.Integer(string="Total Number of Early Leave", compute='_compute_total_time')

    def _compute_total_time(self):
        for record in self:
            total_late_in_sec = total_late_in_min = 0.0
            total_overtime_sec = total_overtime_min = 0.0
            total_number_of_late_in = total_number_of_overtime = total_number_of_early_leave = 0
            total_early_leave_sec = total_early_leave_min = 0.0
            total_late = total_overtime = total_early_leave = False
            for attendance_detail in self.sheet_detail_ids:
                late_attendance_sec =  float(attendance_detail.late_in.split(":")[0]) * 3600 + float(attendance_detail.late_in.split(":")[1]) * 60
                if late_attendance_sec > 0:
                    total_number_of_late_in += 1
                total_late_in_sec += late_attendance_sec

                overtime_sec =  float(attendance_detail.overtime.split(":")[0]) * 3600 + float(attendance_detail.overtime.split(":")[1]) * 60
                if overtime_sec > 0:
                    total_number_of_overtime += 1
                total_overtime_sec += overtime_sec

                early_leave_sec =  float(attendance_detail.early_leave.split(":")[0]) * 3600 + float(attendance_detail.early_leave.split(":")[1]) * 60
                if early_leave_sec > 0:
                    total_number_of_early_leave += 1
                total_early_leave_sec += early_leave_sec

            total_late_in_min = total_late_in_sec / 60
            total_late = "%02d:%02d" % divmod(total_late_in_min, 60)
            record.total_late_in = str(total_late)
            record.total_number_of_late_in = total_number_of_late_in

            total_overtime_min = total_overtime_sec / 60
            total_overtime = "%02d:%02d" % divmod(total_overtime_min, 60)
            record.total_overtime = str(total_overtime)
            record.total_number_of_overtime = total_number_of_overtime

            total_early_leave_min = total_early_leave_sec / 60
            total_early_leave = "%02d:%02d" % divmod(total_early_leave_min, 60)
            record.total_early_leave = str(total_early_leave)
            record.total_number_of_early_leave = total_number_of_early_leave

    @api.onchange('employee_id', 'from_date','to_date')
    def set_name(self):
        self.name = 'Attendance Sheet of ' + str(self.employee_id.name) + ' from ' + str(self.from_date) + ' to ' + str(self.to_date)	

    def generate_attendance_sheet(self):
        sheet_detail_dict = {}
        sheet_detail = self.env['employee.attendace.sheet.detail']
        attendance_objs = self.env['hr.attendance'].search([('employee_id','=',self.employee_id.id),('check_in','>=',self.from_date),('check_out','<=',self.to_date)])
        existing_attendance_detail_objs = self.env['employee.attendace.sheet.detail'].search([('employee_attendace_sheet_id','=',self.id)])
        existing_attendance_detail_objs.unlink()
        if attendance_objs:
            for attendance_obj in attendance_objs:
                check_in_date = datetime.strptime(str(attendance_obj.check_in), DEFAULT_SERVER_DATETIME_FORMAT)
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                check_in_time_date = datetime.strftime(pytz.utc.localize(datetime.strptime(str(attendance_obj.check_in), DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S") 
                check_in_time = datetime.strptime(str(check_in_time_date), '%Y-%m-%d %H:%M:%S')
                check_out_time_date = datetime.strftime(pytz.utc.localize(datetime.strptime(str(attendance_obj.check_out), DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S") 
                check_out_time = datetime.strptime(str(check_out_time_date), '%Y-%m-%d %H:%M:%S')
                since = datetime( check_in_date.year, check_in_date.month, check_in_date.day, 0, 0, 0 )
                #Actual Sign in
                check_in_diff_seconds = (check_in_time-since).total_seconds()
                check_in_diff_minutes = check_in_diff_seconds / 60
                current_user_obj = self.env['res.users'].sudo().search([('id','=',self.env.uid)])

                actual_sign_in = "%02d:%02d" % divmod(check_in_diff_minutes, 60)
                #Actual Sign out
                check_out_diff_seconds = (check_out_time-since).total_seconds()
                check_out_diff_minutes = check_out_diff_seconds / 60
                actual_sign_out = "%02d:%02d" % divmod(check_out_diff_minutes, 60)
                planned_sign_in_minute = attendance_obj.work_schedule.hour_from*60
                planned_sign_in = "%02d:%02d" % divmod(planned_sign_in_minute, 60)
                planned_sign_out_minute = attendance_obj.work_schedule.hour_to*60
                planned_sign_out = "%02d:%02d" % divmod(planned_sign_out_minute, 60)

                allow_late_coming_minute = self.employee_id.company_id.latecoming_consider_time * 60
                overtimer_consider_minute = self.employee_id.company_id.overtime_consider_time * 60
                #Late coming
                if check_in_diff_minutes > planned_sign_in_minute + allow_late_coming_minute:
                    late_in_minute = float(check_in_diff_minutes) - float(planned_sign_in_minute)
                    late_in = "%02d:%02d" % divmod(late_in_minute, 60)
                else:
                    late_in = "%02d:%02d" % divmod(0.0, 60)
                #Overtime
                if check_out_diff_minutes > planned_sign_out_minute + overtimer_consider_minute:
                    overtime_minute = float(check_out_diff_minutes) - float(planned_sign_out_minute)
                    overtime = "%02d:%02d" % divmod(overtime_minute, 60)
                else:
                    overtime = "%02d:%02d" % divmod(0.0, 60)
                #Early going
                if planned_sign_out_minute > check_out_diff_minutes:
                    early_leave_minute = float(planned_sign_out_minute) - float(check_out_diff_minutes)
                    early_leave = "%02d:%02d" % divmod(early_leave_minute, 60)
                else:
                    early_leave = "%02d:%02d" % divmod(0.0, 60)

                sheet_detail_dict = {'employee_attendace_sheet_id': self.id, 'date' : attendance_obj.check_in, 'day' : calendar.day_name[check_in_date.weekday()], 'actual_sign_in' : actual_sign_in,'actual_sign_out' : actual_sign_out, 'planned_sign_in': planned_sign_in, 'planned_sign_out': planned_sign_out, 'late_in': late_in, 'overtime': overtime, 'early_leave': early_leave}
                sheet_detail.create(sheet_detail_dict)

