# -*- coding: utf-8 -*-
from odoo import http

# class BiometricDevice(http.Controller):
#     @http.route('/biometric_device/biometric_device/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/biometric_device/biometric_device/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('biometric_device.listing', {
#             'root': '/biometric_device/biometric_device',
#             'objects': http.request.env['biometric_device.biometric_device'].search([]),
#         })

#     @http.route('/biometric_device/biometric_device/objects/<model("biometric_device.biometric_device"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('biometric_device.object', {
#             'object': obj
#         })