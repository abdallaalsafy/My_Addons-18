# -*- coding: utf-8 -*-
from odoo import models


class QuranAyatDesc(models.Model):
    """Same structure as quran_office.ayat, loaded with the reverse (from An-Nas) page/Juz' data."""
    _name = 'quran_office.ayat_desc'
    _inherit = 'quran_office.ayat'
    _description = 'Model Of Quran Ayat (Reverse Order)'
    _order = 'num_aya_in_quran'
