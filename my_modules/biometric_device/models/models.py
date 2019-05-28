# -*- coding: utf-8 -*-


from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api
import pytz
from datetime import datetime
import datetime as dt
import sys
sys.path.append("zk")
from zk import ZK, const


class BiometricDevice(models.Model):
    _name = 'zk.biometric.device'

    name = fields.Char(string='Name', required=True)
    machine_ip = fields.Char(string='Machine IP', required=True)
    port_no = fields.Integer(string='Port No', required=True)
    device_timezone = fields.Integer(string='Device Timezone', required=True)

    @api.multi
    def device_connect(self):

        zk = ZK(self.machine_ip, port=self.port_no, timeout=5, password=0, force_udp=False, ommit_ping=False)
        print('Connecting to device ...')
        conn = zk.connect()
        return conn

    @api.multi
    def float_to_time(self, time):
        return '{0:02.0f}:{1:02.0f}'.format(*divmod(time * 60, 60))

    @api.multi
    def time_to_float(self, time):
         return int(time.strftime("%H")) + int(time.strftime("%M")) / 60.0

    @api.multi
    def clean_attendance(self):
        self.download_attendance()

        conn = self.device_connect()
        if conn:
            conn.disable_device()
            conn.clear_attendance()
            conn.enable_device()

    @api.multi
    def download_attendance(self):
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']
        hr_employee_obj = self.env['hr.employee']
        res_company = self.env.user.company_id
        conn = self.device_connect()
        device_users = conn.get_users()
        time_def = self.device_timezone

        if conn:
            conn.disable_device()
            attendances = conn.get_attendance()
            attendances.sort(key=lambda a: a.timestamp)
            if attendances:
                for attendance in attendances:
                    atten_time = attendance.timestamp
                    atten_hours = self.time_to_float(atten_time)
                    if atten_hours < res_company.deny_check_in_time_before or atten_hours > res_company.deny_check_out_time_after:
                        continue
                    atten_dayofweek = atten_time.weekday()
                    if atten_dayofweek == 5 or atten_dayofweek == 6:
                        continue
                    atten_date = atten_time.strftime("%Y-%m-%d")
                    atten_time = datetime.strptime(
                        atten_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                    if self.device_timezone < 0:
                        atten_time = atten_time - dt.timedelta(hours=time_def)
                    elif self.device_timezone > 0:
                        atten_time = atten_time - dt.timedelta(hours=time_def)
                    atten_time = datetime.strptime(
                        atten_time.strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S")
                    atten_time = fields.Datetime.to_string(atten_time)
                    hr_employee = None
                    for device_user in device_users:
                        if device_user.user_id == attendance.user_id:
                            hr_employee = hr_employee_obj.search([('device_user_name', '=', device_user.name)])
                            break
                    if hr_employee:
                        duplicate_atten_ids = zk_attendance.search(
                            [('device_user_name', '=', hr_employee[0].device_user_name), ('punching_time', '=', atten_time)])
                        if duplicate_atten_ids:
                            continue
                        else:
                            punch_type = None
                            def_hour = None
                            day_period = None
                            working_hours = hr_employee[0].resource_calendar_id.attendance_ids
                            for working_hour in working_hours:
                                if int(working_hour.dayofweek) == atten_dayofweek:
                                    if working_hour.day_period == "morning" and working_hour.hour_to > atten_hours:
                                        def_hour = self.float_to_time(working_hour.hour_to - time_def)
                                        day_period = "morning"
                                        break
                                    elif working_hour.day_period == "afternoon" and working_hour.hour_from < atten_hours:
                                        def_hour = self.float_to_time(working_hour.hour_from - time_def)
                                        day_period = "afternoon"
                                        break
                            if day_period is None:
                                continue
                            prev_atten_ids = zk_attendance.search(
                                [('device_user_name', '=', hr_employee[0].device_user_name), ('punching_date', '=', atten_date),
                                 ('day_period', '=', day_period)])
                            if prev_atten_ids:
                                att_var = hr_attendance.search([('employee_id', '=', hr_employee[0].id),
                                                                ('check_out', '=', prev_atten_ids[0].punching_time)])
                                if att_var:
                                    if att_var.check_in < datetime.strptime(atten_time, "%Y-%m-%d %H:%M:%S"):
                                        att_var[0].write({'check_out': atten_time})
                                        punch_type = '1'
                            else:
                                if day_period == 'morning':
                                    if datetime.strptime(atten_time, "%Y-%m-%d %H:%M:%S") < datetime.strptime(
                                            atten_date + ' ' + def_hour + ':00', "%Y-%m-%d %H:%M:%S"):
                                        hr_attendance.create({'employee_id': hr_employee[0].id,
                                                              'check_in': atten_time,
                                                              'day_period': day_period,
                                                              'check_out': atten_date + ' ' + def_hour + ':00'})
                                    else:
                                        raise UserError([atten_time, atten_hours])

                                elif day_period == 'afternoon':
                                    if datetime.strptime(atten_time, "%Y-%m-%d %H:%M:%S") > datetime.strptime(
                                            atten_date + ' ' + def_hour + ':00', "%Y-%m-%d %H:%M:%S"):
                                        hr_attendance.create({'employee_id': hr_employee[0].id,
                                                              'check_in': atten_date + ' ' + def_hour + ':00',
                                                              'day_period': day_period,
                                                              'check_out':  atten_time})
                                    else:
                                        raise UserError([atten_time, atten_hours, atten_date + ' ' + def_hour + ':00'])
                                else:
                                    raise UserError(day_period)
                                punch_type = '0'
                            zk_attendance.create({'employee_id': hr_employee[0].id,
                                                  'device_user_name': hr_employee[0].device_user_name,
                                                  'attendance_type': str(attendance.status),
                                                  'punch_type': punch_type,
                                                  'punching_date': atten_date,
                                                  'punching_time': atten_time,
                                                  'day_period': day_period})
                    else:
                        pass
            conn.enable_device()


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    device_user_name = fields.Char(string='Biometric Device User Name')
    day_period = fields.Selection([('morning', 'Morning'),
                                   ('afternoon', 'Afternoon')], string='Day period')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    device_user_name = fields.Char(string='Biometric Device User Name')


class ResCompany(models.Model):
    _inherit = 'res.company'

    deny_check_in_time_before = fields.Float(string='Deny Check in before decided time')
    deny_check_out_time_after = fields.Float(string='Deny Check out after decided time')


