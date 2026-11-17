# -*- coding: utf-8 -*-
from odoo import fields, models


class QuranSurah(models.Model):
    _name = 'quran_office.surah'
    _description = 'Model Of Quran Surah'
    _order = 'surah_num'

    name = fields.Char(string='Name', translate=True)
    surah_num = fields.Integer(string='Sora Num', index=True)
    count_ayat = fields.Integer(string='Count Ayat')

    def get_correct_ayah_of_surah(self, ayah_num):
        """Clamp the ayah number between 1 and the number of ayat of the surah."""
        self.ensure_one()
        return max(1, min(ayah_num, self.count_ayat))
