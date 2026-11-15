# -*- coding: utf-8 -*-
import math

from odoo import api, fields, models

# Memorization methods (numeric codes used by the calculation helpers)
METHOD_FROM_NAS = 0      # Reverse memorization, starting from An-Nas
METHOD_FROM_BAQARAH = 1  # Forward memorization, starting from Al-Baqarah
METHOD_MIXED = 2         # Mixed memorization (no fixed direction)

FATIHA_NUM = 1           # Surah number of Al-Fatiha
LAST_CHAPTER = 30        # Last Juz' (chapter) of the Quran
TOTAL_JUZ = 30


class QuranAyat(models.Model):
    """
    One record per ayah. The same data is loaded twice:
      * quran_office.ayat       -> pages/Juz' counted forward (from Al-Baqarah)
      * quran_office.ayat_desc  -> pages/Juz' counted in reverse (from An-Nas)
    A "chapter" is a Juz' of about 20 pages, `num_page_in_chapter` is the page
    index inside it, so (chapter - 1 + page / count_pages) is the amount in Juz'.
    """
    _name = 'quran_office.ayat'
    _description = 'Model Of Quran Ayat'
    _order = 'num_aya_in_quran'

    num_aya_in_quran = fields.Integer(string='Num Aya In Quran', index=True)

    surah_id = fields.Many2one('quran_office.surah', string='Surah', index=True)
    num_aya_in_surah = fields.Integer(string='Num Aya In Surah', index=True)

    chapter_num = fields.Integer(string='Chapter Num', index=True)
    num_aya_in_chapter = fields.Integer(string='Num Aya In Chapter')
    count_ayat_in_chapter = fields.Integer(string='Count Ayat In Chapter')

    num_page_in_chapter = fields.Integer(string='Num Page In Chapter')
    count_pages_in_chapter = fields.Integer(string='Count Page In Chapter')

    page_num = fields.Integer(string='Page Num')

    # ============================== Display =====================================
    @api.depends('surah_id.name', 'num_aya_in_surah')
    def _compute_display_name(self):
        for record in self:
            record.display_name = '%s - %s' % (record.surah_id.name or '', record.num_aya_in_surah)

    # ============================== Helpers =====================================
    @api.model
    def get_memorization_method(self, method):
        method_dict = {
            'from_nas': METHOD_FROM_NAS,
            'from_baqarah': METHOD_FROM_BAQARAH,
            'mixed': METHOD_MIXED,
        }
        return method_dict.get(method, METHOD_MIXED)

    @api.model
    def _get_ayat_model(self, method):
        """Model holding the data of the given (numeric) method."""
        return 'quran_office.ayat_desc' if method == METHOD_FROM_NAS else 'quran_office.ayat'

    @api.model
    def _get_effective_pages(self, method, chapter_num, count_pages):
        """
        Number of pages of a chapter that count in the amount.
        In the reverse method Al-Fatiha is calculated before An-Nas (apart from
        the chapters), so the last chapter has one page less.
        """
        if method == METHOD_FROM_NAS and chapter_num == LAST_CHAPTER:
            return count_pages - 1
        return count_pages

    # ============================== Calculations =====================================
    @api.model
    def calc_juze_amount(self, method, surah,surah_ids, ayah):
        """
        Calculate the memorization amount in Juz' from surah (id) and ayah number
        method = 0  ===>> Reverse Memorization From El-Nas
        method = 1  ===>> Forward Memorization From El-Baqrah
        method = 2  ===>> Mixed Memorization
        """
        method = self.get_memorization_method(method)
        if method == METHOD_MIXED:
            return self.calc_juze_amount_from_surahs(method, surah_ids)
        
        if not ayah or not surah:
            return 0.0

        surah_record = self.env['quran_office.surah'].browse(surah).exists()
        if not surah_record:
            return 0.0
        if surah_record.surah_num == FATIHA_NUM:
            method = METHOD_FROM_BAQARAH

        record_ayah = self.env[self._get_ayat_model(method)].search(
            [('surah_id', '=', surah_record.id), ('num_aya_in_surah', '=', ayah)], limit=1)
        if not record_ayah:
            return 0.0

        count_pages = self._get_effective_pages(
            method, record_ayah.chapter_num, record_ayah.count_pages_in_chapter)
        if count_pages <= 0:
            return 0.0

        return round(record_ayah.chapter_num - 1 + record_ayah.num_page_in_chapter / count_pages, 2)

    @api.model
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
        fatiha_ids = surahs.filtered(lambda s: s.surah_num == FATIHA_NUM).ids
        other_ids = [sid for sid in surahs.ids if sid not in fatiha_ids]

        pages = {}  # (model, chapter_num, page_num) -> weight of the page in Juz'

        def collect(model_method, ids):
            if not ids:
                return
            model_name = self._get_ayat_model(model_method)
            rows = self.env[model_name].search_read(
                [('surah_id', 'in', ids)],
                ['chapter_num', 'page_num', 'count_pages_in_chapter'],
            )
            for row in rows:
                count_pages = self._get_effective_pages(
                    model_method, row['chapter_num'], row['count_pages_in_chapter'])
                if count_pages > 0:
                    pages[(model_name, row['chapter_num'], row['page_num'])] = 1.0 / count_pages

        collect(METHOD_FROM_BAQARAH, fatiha_ids)
        collect(METHOD_FROM_NAS if method == METHOD_FROM_NAS else METHOD_FROM_BAQARAH, other_ids)

        # Al-Fatiha is calculated apart in the reverse method, so never exceed the whole Quran
        return round(min(sum(pages.values()), float(TOTAL_JUZ)), 2)

    @api.model
    def calc_surah_ayah_from_amount(self, method, amount_juz):
        """
        Calculate surah and ayah (the last ayah of the reached page) from the amount in Juz'
        method = 0  ===>> Reverse Memorization From El-Nas
        method = 1  ===>> Forward Memorization From El-Baqrah
        method = 2  ===>> Mixed Memorization
        """
        empty = {'surah_id': False, 'ayah_num': 0}
        method = self.get_memorization_method(method)
        if not amount_juz or amount_juz <= 0 or amount_juz > TOTAL_JUZ or method == METHOD_MIXED:
            return empty

        Ayat = self.env[self._get_ayat_model(method)]
        chapter_num = math.ceil(amount_juz)
        first_ayah = Ayat.search([('chapter_num', '=', chapter_num)], limit=1)
        count_pages = self._get_effective_pages(
            method, chapter_num, first_ayah.count_pages_in_chapter)
        if not first_ayah or count_pages <= 0:
            return empty

        # The amount is rounded to 2 decimals, so round (not truncate) to get the page back
        num_page = round((amount_juz - chapter_num + 1) * count_pages)
        num_page = max(1, min(count_pages, num_page))

        record_ayah = Ayat.search(
            [('chapter_num', '=', chapter_num), ('num_page_in_chapter', '=', num_page)],
            order='num_aya_in_quran desc', limit=1)
        if not record_ayah:
            return empty

        return {'surah_id': record_ayah.surah_id.id, 'ayah_num': record_ayah.num_aya_in_surah}
