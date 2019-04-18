# -*- coding: utf-8 -*-
from odoo import http

# class Lis(http.Controller):
#     @http.route('/lis/lis/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lis/lis/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lis.listing', {
#             'root': '/lis/lis',
#             'objects': http.request.env['lis.lis'].search([]),
#         })

#     @http.route('/lis/lis/objects/<model("lis.lis"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lis.object', {
#             'object': obj
#         })