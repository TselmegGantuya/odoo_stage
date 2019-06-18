# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api
from datetime import datetime
import datetime as dt
from .zk import ZK, const


class BiometricDevice(models.Model):
    _name = 'zk.biometric.device'
    _description = "Model for interacting with the biometric device attendance"

    name = fields.Char(string='Name', required=True)
    machine_ip = fields.Char(string='Machine IP', required=True)
    port_no = fields.Integer(string='Port No', required=True)
    device_timezone = fields.Integer(string='Device Timezone', required=True)

    '''
    Function used to connect with device
    This way we can only create a ZK object in a single place
    '''
    @api.multi
    def device_connect(self):
        zk = ZK(self.machine_ip, port=self.port_no, timeout=5, password=0, force_udp=False, ommit_ping=False)
        print('Connecting to device ...')
        conn = zk.connect()
        return conn

    '''
        Function used to convert float to string in format of H:M
    '''
    @api.multi
    def float_to_time(self, time):
        return '{0:02.0f}:{1:02.0f}'.format(*divmod(time * 60, 60))

    '''
        Function used to datetime to float
    '''
    @api.multi
    def time_to_float(self, time):
        return int(time.strftime("%H")) + int(time.strftime("%M")) / 60.0

    '''
        Function used to clean all the data from biometric device
    '''
    @api.multi
    def clean_attendance(self):
        self.download_attendance()

        conn = self.device_connect()
        if conn:
            conn.disable_device()
            conn.clear_attendance()
            conn.enable_device()

    '''
        Function used to download all attendances data to attendance log
        This way was used so that we can put attendances data in attendance log from multiple sources(Downlaod, Import)
    '''
    @api.multi
    def download_attendance(self):
        zk_attendance = self.env['zk.machine.attendance']
        hr_employee_obj = self.env['hr.employee']
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
                    atten_time = datetime.strptime(
                        atten_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                    atten_time = atten_time - dt.timedelta(hours=time_def)
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
                            zk_attendance.create({'employee_id': hr_employee[0].id,
                                                  'device_user_name': hr_employee[0].device_user_name,
                                                  'attendance_type': str(attendance.status),
                                                  'punching_time': atten_time})
                    else:
                        pass
            conn.enable_device()

    '''
        Function used to create new attendance record based on attendance logs
    '''
    def make_attendance(self):
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']
        hr_employee_obj = self.env['hr.employee']
        res_company = self.env.user.company_id
        time_def = self.device_timezone

        for attendance in zk_attendance.search([]):
            if attendance.employee_id:
                pass
            else:
                hr_employee = hr_employee_obj.search([('device_user_name', '=', attendance.device_user_name)])
                if hr_employee:
                    attendance.write({'employee_id': hr_employee.id})
                else:
                    continue

            atten_time = attendance.punching_time
            atten_hours = self.time_to_float(atten_time)
            if atten_hours + time_def < res_company.deny_check_in_time_before or atten_hours + time_def > res_company.deny_check_out_time_after:
                continue
            atten_dayofweek = atten_time.weekday()
            atten_date = atten_time.strftime('%Y-%m-%d')
            day_period = None
            def_hour = None
            working_hours = attendance.employee_id.resource_calendar_id.attendance_ids
            for working_hour in working_hours:
                if int(working_hour.dayofweek) == atten_dayofweek:
                    if working_hour.day_period == "afternoon":
                        if atten_hours < working_hour.hour_to - time_def:
                            def_hour = self.float_to_time(working_hour.hour_to - time_def)
                            day_period = 'morning'
                            break
                        elif atten_hours + time_def > working_hour.hour_from:
                            def_hour = self.float_to_time(working_hour.hour_from - time_def)
                            day_period = 'afternoon'
                            break
            prev_atten_ids = hr_attendance.search(
                [('employee_id', '=', attendance.employee_id.id),
                 ('attendance_date', '=', atten_date)])
            if prev_atten_ids:
                if prev_atten_ids[0].check_in > atten_time:
                    prev_atten_ids[0].write({'check_in': atten_time,
                                             'check_in_hour': self.time_to_float(atten_time) + time_def})
                elif prev_atten_ids[0].check_out < atten_time:
                    prev_atten_ids[0].write({'check_out': atten_time,
                                             'check_out_hour': self.time_to_float(atten_time) + time_def})
            else:
                if day_period == 'morning':
                    if self.time_to_float(datetime.strptime(def_hour, '%H:%M')) > self.time_to_float(atten_time):
                        hr_attendance.create({'employee_id': attendance.employee_id.id,
                                              'check_in': atten_time,
                                              'attendance_date': atten_date,
                                              'check_in_hour': self.time_to_float(atten_time) + time_def,
                                              'check_out_hour': self.time_to_float(datetime.strptime(def_hour, '%H:%M')) + time_def,
                                              'state': 0,
                                              'check_out': atten_date + ' ' + def_hour + ':00'})
                if day_period == 'afternoon':
                    hr_attendance.create({'employee_id': attendance.employee_id.id,
                                          'check_in': atten_date + ' ' + def_hour + ':00',
                                          'attendance_date': atten_date,
                                          'check_in_hour': self.time_to_float(datetime.strptime(def_hour, '%H:%M')) + time_def,
                                          'check_out_hour': self.time_to_float(atten_time) + time_def,
                                          'state': 0,
                                          'check_out': atten_time})


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    department_id = fields.Many2one('hr.department', string="Department")
    device_user_name = fields.Char(string='Biometric Device User Name')
    state = fields.Selection([(0, 'Auto Input'), (1, 'Manual input'), (2, 'Done'), (3, 'Cancelled')], default=0,
                             string='State')
    attendance_date = fields.Date(string='Date')
    check_in_hour = fields.Float(string='Check in hour')
    check_out_hour = fields.Float(string="Check out hour")

    @api.onchange('check_in', 'check_out')
    def _onchange_attendance(self):
        if self.state == 0:
            self.state = 1


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    device_user_name = fields.Char(string='Biometric Device User Name')


class ResCompany(models.Model):
    _inherit = 'res.company'

    deny_check_in_time_before = fields.Float(string='Deny Check in before decided time')
    deny_check_out_time_after = fields.Float(string='Deny Check out after decided time')


