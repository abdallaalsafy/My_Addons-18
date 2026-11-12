
from odoo import models, fields,api, _
from odoo.exceptions import ValidationError, UserError

class MemorizationMixin(models.AbstractModel):
    _name = 'memorization.mixin'
    _description = 'Memorization Mixin'


    surah_id = fields.Many2one(
            'quran_office.surah',
            'Surah',
            help="Surah where memorization starts"
        )
    ayah_num = fields.Integer(
            'Ayah',
            help="Ayah number where memorization starts"
        )
    juze_amount = fields.Float(
            string='Amount (Juz\')',
            compute='_compute_juze_amount',
            inverse='_inverse_juze_amount',
            store=True,
            digits=(16, 2),
            help="Amount of Quran memorized in Juz' (parts) with decimal precision"
        )
    surah_ids = fields.Many2many(
            'quran_office.surah',
            string='Surahs',
            help="Surahs that must be memorized"
        )
    memorization_method = fields.Selection([
            ('from_baqarah', 'Memorization from Al-Baqarah'),
            ('from_nas', 'Memorization from An-Nas'),
            ('mixed', 'Mixed Memorization'),
        ], 'Memorization Method', default='from_nas', required=True,
            help="Method of Quran memorization")

# ============================== OnChange Functions =====================================
    @api.onchange('surah_id', 'ayah_num', 'memorization_method')
    def _onchange_surah_id_ayah(self):
        """Validate that ayah number is within the surah's ayat count."""
        surah_id = self.surah_id
        ayah_num = self.ayah_num
        if self.memorization_method == 'mixed':
            self.surah_id = False
            self.ayah_num = 0
        else:
            self.surah_ids = False
            if surah_id:
                self.ayah_num = surah_id.get_correct_ayah_of_surah(ayah_num)

# ============================== Compute Functions =====================================
    @api.depends('memorization_method', 'surah_id', 'surah_ids', 'ayah_num')
    def _compute_juze_amount(self):
        """
        Calculate memorization amount in Juz' (parts) based on memorization method and ayah position.
        Quran has 6236 ayahs total, divided into 30 Juz' (each Juz' ≈ 207.87 ayahs).
        """
        for record in self:
            if record.env.context.get('skip_compute_juz'):
                continue
            record.juze_amount = self.env['quran_office.ayat'].calc_juze_amount(record.memorization_method, record.surah_id.id, record.surah_ids, record.ayah_num)

    def _inverse_juze_amount(self):
        """ Calculate memorization surah and ayah based on memorization amount in Juz' """
        for record in self:
            result = self.env['quran_office.ayat'].calc_surah_ayah_from_amount(record.memorization_method, record.juze_amount)
            if result['surah_id'] == False or result['ayah_num'] == 0:
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
        if not self._check_memorization_amount() and self.memorization_method == 'mixed':
            raise ValidationError(_('Select memorization Surahs for mixed method'))  
           
    def _check_ayah_num(self):
        """Constraint to ensure ayah number is valid for the selected surah."""
        for record in self:
            if not (record.surah_id and record.ayah_num > 0):
                return False
            if record.ayah_num > record.surah_id.count_ayat:
                return False
            return True

    def _check_memorization_amount(self):
        for record in self:
            if record.juze_amount <= 0 or  record.juze_amount > 30:
                return False
            return True