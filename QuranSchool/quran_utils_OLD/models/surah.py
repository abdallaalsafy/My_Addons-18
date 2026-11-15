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


    def get_correct_ayah_of_surah(self, ayah_num):
        if ayah_num < 1:
            return 1
        elif ayah_num > self.count_ayat:
            return self.count_ayat
        return ayah_num