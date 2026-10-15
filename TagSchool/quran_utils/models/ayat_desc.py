# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class QuranAyatDesc(models.Model):
    _name = 'quran_office.ayat_desc'
    _inherit = 'quran_office.ayat'
    _order = 'num_aya_in_quran'





