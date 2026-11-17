# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

class MemorizationMixin(models.AbstractModel):
    _name = 'memorization.mixin'
    _description = 'Memorization Mixin'

    surah_id = fields.Many2one(
        'quran_office.surah',
        'Memorization Surah',
        help="Surah where memorization starts",
    )
    ayah_num = fields.Integer(
        'Memorization Ayah',
        help="Ayah number where memorization starts",
    )
    juze_amount = fields.Float(
        string='Memorization Amount (Juz\')',
        compute='_compute_juze_amount',
        inverse='_inverse_juze_amount',
        store=True,
        digits=(16, 2),
        help="Amount of Quran memorized in Juz' (parts) with decimal precision",
    )
    surah_ids = fields.Many2many(
        'quran_office.surah',
        string='Required Surahs',
        help="Surahs that must be memorized",
    )
    memorization_method = fields.Selection([
        ('from_baqarah', 'Memorization from Al-Baqarah'),
        ('from_nas', 'Memorization from An-Nas'),
        ('mixed', 'Mixed Memorization'),
    ], 'Memorization Method', default='from_nas', required=True,
        help="Method of Quran memorization")

    # ============================== OnChange Functions =====================================
    @api.onchange('surah_id', 'ayah_num')
    def _onchange_surah_id_ayah(self):
        """Keep the ayah number within the surah's ayat count."""
        for record in self:
            if record.surah_id:
                record.ayah_num = record.surah_id.get_correct_ayah_of_surah(record.ayah_num)

    # ============================== Compute Functions =====================================
    @api.depends('memorization_method', 'surah_id', 'surah_ids', 'ayah_num')
    def _compute_juze_amount(self):
        """Memorization amount in Juz' from the memorization method and the ayah position."""
        Ayat = self.env['quran_office.ayat']
        for record in self:
            if record.env.context.get('skip_compute_juz'):
                continue
            record.juze_amount = Ayat.calc_juze_amount(
                record.memorization_method, record.surah_id.id, record.surah_ids.ids, record.ayah_num)

    def _inverse_juze_amount(self):
        """Memorization surah and ayah from the memorization amount in Juz'."""
        Ayat = self.env['quran_office.ayat']
        for record in self:
            if record.surah_id and record.ayah_num > 0:
                current = Ayat.calc_juze_amount(
                    record.memorization_method, record.surah_id.id,
                    record.surah_ids.ids, record.ayah_num)
                if float_compare(current, record.juze_amount, precision_digits=2) == 0:
                    continue

            result = Ayat.calc_surah_ayah_from_amount(record.memorization_method, record.juze_amount)
            if not result['surah_id'] or not result['ayah_num']:
                continue
            record.with_context(skip_compute_juz=True).update({
                'surah_id': result['surah_id'],
                'ayah_num': result['ayah_num'],
            })

    # ======================= Helper Functions =========================
    def _check_memorization_amount_consistency(self):
        """Validate memorization amount consistency with surah and ayah calculation."""
        if self.memorization_method != 'mixed':
            if not self._check_memorization_amount() and not self._check_ayah_num():
                raise ValidationError(_('Memorization amount and surah and ayah is required for this type of method'))
            
    def _constrain_memorization_amount(self):
        """Mixed method: the memorized amount is defined by the selected Surahs
        (juze_amount is not computed/edited for this method)."""
        for record in self:
            if record.memorization_method == 'mixed' and not record.surah_ids:
                raise ValidationError(_('Select memorization Surahs for mixed method'))

    def _check_ayah_num(self):
        """True if every record has an ayah number valid for its selected surah."""
        return all(
            record.surah_id and 0 < record.ayah_num <= record.surah_id.count_ayat
            for record in self
        )

    def _check_memorization_amount(self):
        """True if every record has a memorization amount between 0 (excluded) and 30."""
        return all(0 < record.juze_amount <= 30 for record in self)
