# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Patient (models.Model):
    _name = 'lis.patient'
    _description = "The Patient"

    name = fields.Char()
    birth_date = fields.Date()
    age = fields.Integer()
    sex = fields.Selection(selection=["Male", "Female"])

    order_ids = fields.One2many('lis.order', 'patient_id', string='Order_patient')


class Order (models.Model):
    _name = 'lis.order'

    description = fields.Char()

    patient_id = fields.Many2one('lis.patient', ondelete='cascade', string='Patient')
    sample_id = fields.Many2one('lis.sample', ondelete='cascade', string='Sample')
    result_ids = fields.One2many('lis.result', 'order_id', string='Test')


class Sample (models.Model):
    _name = 'lis.sample'

    volume = fields.Float()
    sample_position = fields.Integer()

    order_ids = fields.One2many('lis.order', 'sample_id', string='Order_sample')


class Result (models.Model):
    _name = 'lis.result'

    type = fields.Char()
    comments = fields.Char()

    order_id = fields.Many2one('lis.order', ondelete='cascade', string='Order_test')
    test_id = fields.Many2one('lis.test', ondelete='cascade', string='Order_test')


class Test (models.Model):
    _name = 'lis.test'

    name = fields.Char()
    type = fields.Char()

    result_ids = fields.One2many('lis.result', 'test_id', string='Order_test')
