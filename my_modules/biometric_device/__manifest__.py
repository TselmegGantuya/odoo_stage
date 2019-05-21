# -*- coding: utf-8 -*-
{
    'name': "Biometric device",

    'summary': """
        Biometric device module that is meant to connect attendance module and Biometric device""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base_setup', 'hr_attendance'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/zk_device_view.xml',
        'views/zk_machine_attendance_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}