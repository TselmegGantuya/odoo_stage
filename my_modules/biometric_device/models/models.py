# -*- coding: utf-8 -*-


from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api
import pytz
from datetime import datetime
import sys
sys.path.append("zk")
from zk import ZK, const


class BiometricDevice(models.Model):
    _name = 'zk.biometric.device'

    name = fields.Char(string='Name', required=True)
    machine_ip = fields.Char(string='Machine IP', required=True)
    port_no = fields.Integer(string='Port No', required=True)

    @api.multi
    def device_connect(self):

        zk = ZK(self.machine_ip, port=self.port_no, timeout=5, password=0, force_udp=False, ommit_ping=False)
        print('Connecting to device ...')
        conn = zk.connect()
        return conn

    @api.multi
    def download_attendance(self):
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']
        hr_employee = self.env['hr.employee']
        conn = self.device_connect()
        device_users = conn.get_users()

        if conn:
            conn.disable_device()
            attendances = conn.get_attendance()
            if attendances:
                for attendance in attendances:
                    atten_time = attendance.timestamp
                    atten_date = atten_time.strftime("%Y-%m-%d")
                    atten_time = datetime.strptime(
                        atten_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                    local_tz = pytz.timezone(
                        self.env.user.partner_id.tz or 'GMT')
                    local_dt = local_tz.localize(atten_time, is_dst=False )
                    utc_dt = local_dt.astimezone(pytz.utc)
                    utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                    atten_time = datetime.strptime(
                        utc_dt, "%Y-%m-%d %H:%M:%S")
                    atten_time = fields.Datetime.to_string(atten_time)
                    hr_user = None
                    for device_user in device_users:
                        if device_user.user_id == attendance.user_id:
                            hr_user = hr_employee.search([('device_user_name', '=', device_user.name)])
                    if hr_user:
                        duplicate_atten_ids = zk_attendance.search(
                            [('device_user_name', '=', attendance.user_id), ('punching_time', '=', atten_time)])
                        if duplicate_atten_ids:
                            continue
                        else:
                            prev_atten_ids = zk_attendance.search(
                                [('device_user_name', '=', attendance.user_id), ('punching_date', '=', atten_date)])
                            punch_type = None
                            if prev_atten_ids:
                                att_var = hr_attendance.search([('employee_id', '=', hr_user[0].id),
                                                                ('check_in', '=', prev_atten_ids[-1].punching_time)])
                                if att_var:
                                    att_var[-1].write({'check_out': atten_time})
                                    punch_type = '1'
                            else:
                                hr_attendance.create({'employee_id': hr_user[0].id,
                                                      'check_in': atten_time,
                                                      'check_out': atten_date + ' 23:00:00'})
                                punch_type = '0'
                            zk_attendance.create({'employee_id': hr_user[0].id,
                                                  'device_user_name': attendance.user_id,
                                                  'attendance_type': str(attendance.status),
                                                  'punch_type': punch_type,
                                                  'punching_date': atten_date,
                                                  'punching_time': atten_time})
                    else:
                        pass


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    device_user_name = fields.Char(string='Biometric Device User Name')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    device_user_name = fields.Char(string='Biometric Device User Name')
