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


    def get_memorization_method(self, method):
        method_dict = {'from_nas': 0,'from_baqarah': 1,'mixed': 2,}
        return method_dict.get(method, 2)
    
    def calc_juze_amount(self, method, surah, surah_ids, ayah):
        """
        Calculate surah and ayah from memorization method and amount in Juz'
        method = 0  ===>> Reverse Memorization From El-Nas
        method = 1  ===>> Forward Memorization From El-Baqrah
        method = 2  ===>> Mixed Memorization
        """
        method = self.get_memorization_method(method)

        if method == 2:
            return self.calc_juze_amount_from_surahs(method, surah_ids)
        
        if not ayah or not surah:
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

    def calc_surah_ayah_from_amount(self, method, juze_amount):
        """
        Calculate surah and ayah from memorization method and amount in Juz'
        method = 0  ===>> Reverse Memorization From El-Nas
        method = 1  ===>> Forward Memorization From El-Baqrah
        method = 2  ===>> Mixed Memorization
        """
        method = self.get_memorization_method(method)
        
        if not juze_amount or juze_amount <= 0 or method == 2:
            return {'surah_id': False, 'ayah_num': 0}

        chapter_num = math.ceil(juze_amount)
        if method == 0: # Reverse Memorization From El-Nas
            model_ayah = 'quran_office.ayat_desc'
        else: # Forward Memorization From El-Baqrah
            model_ayah = 'quran_office.ayat'

        record_ayah = self.env[model_ayah].search([('chapter_num', '=', chapter_num)], limit=1)
        count_pages_in_chapter = record_ayah.count_pages_in_chapter
        if chapter_num == 30 and method == 0:
            count_pages_in_chapter -= 1

        num_page_in_chapter = int((juze_amount - chapter_num + 1) * count_pages_in_chapter)
        record_ayah = self.env[model_ayah].search(
            [('chapter_num', '=', chapter_num), ('num_page_in_chapter', '=', num_page_in_chapter)],order='id desc', limit=1)
        print(record_ayah.id)

        if not record_ayah:
            return {'surah_id': False, 'ayah_num': 0}

        return {'surah_id': record_ayah.surah_id.id, 'ayah_num': record_ayah.num_aya_in_surah}

    def calc_juze_amount_from_surahs(self, method, surah_ids):
        """
        Calculate the total amount (in Juz') of several scattered surahs.
        surah_ids: list of ids or a recordset of 'quran_office.surah'
        method = 0  ===>> Reverse Memorization From El-Nas
        method = 1  ===>> Forward Memorization From El-Baqrah
        method = 2  ===>> Mixed Memorization (calculated as forward)

        Every physical page touched by the selected surahs counts once, with a
        weight of 1 / count_pages_in_chapter of the chapter (Juz') it belongs to.
        A page shared by two surahs (or two Juz') is never counted twice.
        """
        method = self.get_memorization_method(method)
        if hasattr(surah_ids, 'ids'):
            surah_ids = surah_ids.ids
        surah_ids = list(set(surah_ids or []))
        if not surah_ids:
            return 0.0

        # Al-Fatiha is always calculated from the forward data (same as calc_juze_amount)
        surahs = self.env['quran_office.surah'].browse(surah_ids).exists()
        fatiha_ids = surahs.filtered(lambda s: s.surah_num == 1).ids
        other_ids = [sid for sid in surahs.ids if sid not in fatiha_ids]

        pages = {}  # (model, chapter_num, page_num) -> weight of the page in Juz'

        def collect(model_name, ids, fix_last_chapter=False):
            if not ids:
                return
            rows = self.env[model_name].search_read(
                [('surah_id', 'in', ids)],
                ['chapter_num', 'page_num', 'count_pages_in_chapter'],
            )
            for row in rows:
                count_pages = row['count_pages_in_chapter']
                # because Al-Fatiha calculated before El-Nas in the reverse memorization
                if fix_last_chapter and row['chapter_num'] == 30:
                    count_pages -= 1
                if count_pages > 0:
                    pages[(model_name, row['chapter_num'], row['page_num'])] = 1.0 / count_pages

        collect('quran_office.ayat', fatiha_ids)
        if method == 0:  # Reverse Memorization From El-Nas
            collect('quran_office.ayat_desc', other_ids, fix_last_chapter=True)
        else:  # Forward / Mixed
            collect('quran_office.ayat', other_ids)

        # Al-Fatiha is calculated apart in the reverse method, so never exceed the whole Quran
        return round(min(sum(pages.values()), 30.0), 2)
    
        

