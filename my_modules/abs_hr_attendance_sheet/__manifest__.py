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

{
    'name'    : "Attendance Sheet",
    'author'  : 'Ascetic Business Solution',
    'category': 'Human Resources',
    'summary' : """Quick access of Employee's Attendance""",
    'license' : 'OPL-1',
    'price'   : 55.00,
    'currency': "EUR",
    'website' : 'http://www.asceticbs.com',
    'description': """ """,
    'version' : '12.0',
    'depends' : ['hr_attendance','hr_contract','hr_payroll'],
    'data'    : [
                 'security/ir.model.access.csv',
                 'views/res_company_view.xml',
                 'views/hr_attendance_view.xml',
                 'views/salary_rule.xml',
                 'report/report_view.xml',
                 'report/attendance_sheet_report.xml'
                ],
    'images'  : ['static/description/banner.png'],
    'live_test_url': "http://www.test.asceticbs.com/web/database/selector",
    'installable'  : True,
    'application'  : True,
    'auto_install' : False,
}
