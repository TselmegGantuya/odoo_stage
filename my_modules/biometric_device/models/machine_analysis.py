# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: cybrosys(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
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
###################################################################################
from odoo import tools
from odoo import models, fields, api, _

class ZkMachine(models.Model):
    _name = 'zk.machine.attendance'
    _order = 'punching_time asc'
    _description = "Model for saving the biometric device attendance on the application"

    employee_id = fields.Many2one('hr.employee', string="Employee", ondelete='cascade', index=True)
    device_user_name = fields.Char(string='Biometric Device User Name')

    attendance_type = fields.Selection([('1', 'Finger'),
                                        ('15', 'Face')], string='Category')
    punching_time = fields.Datetime(string='Punching Time')



