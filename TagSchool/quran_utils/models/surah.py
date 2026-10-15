# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class cls_soras(models.Model):
    _name = 'quran_office.surah'
    _description = 'Model Of Quran Surah'
    _order = 'surah_num'

    name = fields.Char(string='Name', translate=True)
    surah_num = fields.Integer(string='Sora Num')
    count_ayat = fields.Integer(string='Count Ayat')