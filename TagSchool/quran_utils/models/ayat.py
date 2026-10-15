# -*- coding: utf-8 -*-
import math

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class QuranAyat(models.Model):
    _name = 'quran_office.ayat'
    _description = 'Model Of Quran Ayat'
    _order = 'num_aya_in_quran'

    num_aya_in_quran = fields.Integer(string='Num Aya In Quran')

    surah_id = fields.Many2one('quran_office.surah', string='Surah')
    num_aya_in_surah = fields.Integer(string='Num Aya In Surah')

    chapter_num = fields.Integer(string='Chapter Num')
    num_aya_in_chapter = fields.Integer(string='Num Aya In Chapter')
    count_ayat_in_chapter = fields.Integer(string='Count Ayat In Chapter')

    num_page_in_chapter = fields.Integer(string='Num Page In Chapter')
    count_pages_in_chapter = fields.Integer(string='Count Page In Chapter')

    page_num = fields.Integer(string='Page Num')



    def calc_memorization_amount_juz(self, method, surah, ayah):
        """
        Calculate surah and ayah from memorization method and amount in Juz'
        method = 0  ===>> Reverse Memorization From El-Nas
        method = 1  ===>> Forward Memorization From El-Baqrah
        method = 2  ===>> Mixed Memorization
        """
        if not ayah or not surah or method ==2:
            return 0

        if surah == 1:# Surah Al-Fatiha
            method = 1

        if method == 0: # Reverse Memorization From El-Nas
            record_ayah = self.env['quran_office.ayat_desc'].search([('surah_id', '=', surah), ('num_aya_in_surah', '=', ayah)])
        else: # Forward Memorization From El-Baqrah
            record_ayah = self.env['quran_office.ayat'].search([('surah_id', '=', surah), ('num_aya_in_surah', '=', ayah)])

        if not record_ayah:
            return 0
        
        num_page_in_chapter = record_ayah.num_page_in_chapter
        chapter_num = record_ayah.chapter_num
        count_pages_in_chapter = record_ayah.count_pages_in_chapter

        # because Al-Fatiha calculated before El-Nas in the reverse memorization
        if chapter_num == 30 and method == 0:
            count_pages_in_chapter -= 1

        return round(chapter_num - 1 + (num_page_in_chapter/count_pages_in_chapter),2)

    def calc_surah_ayah_from_amount(self, method, amount_juz):
        """
        Calculate surah and ayah from memorization method and amount in Juz'
        method = 0  ===>> Reverse Memorization From El-Nas
        method = 1  ===>> Forward Memorization From El-Baqrah
        method = 2  ===>> Mixed Memorization
        """
        if not amount_juz or amount_juz <= 0 or method == 2:
            return {'surah_id': False, 'ayah_num': 0}

        chapter_num = math.ceil(amount_juz)
        if method == 0: # Reverse Memorization From El-Nas
            model_ayah = 'quran_office.ayat_desc'
        else: # Forward Memorization From El-Baqrah
            model_ayah = 'quran_office.ayat'

        record_ayah = self.env[model_ayah].search([('chapter_num', '=', chapter_num)], limit=1)
        count_pages_in_chapter = record_ayah.count_pages_in_chapter
        if chapter_num == 30 and method == 0:
            count_pages_in_chapter -= 1

        num_page_in_chapter = int((amount_juz - chapter_num + 1) * count_pages_in_chapter)
        record_ayah = self.env[model_ayah].search(
            [('chapter_num', '=', chapter_num), ('num_page_in_chapter', '=', num_page_in_chapter)],order='id desc', limit=1)
        print(record_ayah.id)

        if not record_ayah:
            return {'surah_id': False, 'ayah_num': 0}

        return {'surah_id': record_ayah.surah_id.id, 'ayah_num': record_ayah.num_aya_in_surah}

