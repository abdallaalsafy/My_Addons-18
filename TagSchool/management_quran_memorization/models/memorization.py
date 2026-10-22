# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import calendar

class StudentMemorization(models.Model):
    _name = 'student.memorization'
    _description = 'Student Monthly Quran Memorization'
    _order = 'memorization_month desc, student_id'

    # Sequence Details
    name = fields.Char(
        string='Memorization Number',
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    # ============== Basic Information from student ===========================
    student_id = fields.Many2one(
        'res.partner', 
        string='Student Name',
        required=True,
        domain="[('is_student', '=', True)]"
    )
    # Related Fields (computed from student)
    office_id = fields.Many2one(
        'quran.office.office',
        string='Student Office',
    )
    class_id = fields.Many2one(
        'quran_office.class',
        string='Student Class',
        domain="[('office_id', '=?', office_id)]",
    )
    teacher_id = fields.Many2one(
        'res.partner',
        string='Student Teacher',
        domain="[('is_teacher', '=', True)]"
    )
    # Memorization Details
    memorization_method = fields.Selection([
        ('from_baqarah', 'Memorization from Al-Baqarah'),
        ('from_nas', 'Memorization from An-Nas'),
        ('mixed', 'Mixed Memorization'),
    ], 'Memorization Method', default='from_nas', required=True,
        help="Method of Quran memorization")

    # ================= Basic Fields Of Memorization =========================
    memorization_surah = fields.Many2one(
        'quran_office.surah',
        'Memorization Surah',
        help="Surah where memorization starts"
    )
    memorization_ayah = fields.Integer(
        'Memorization Ayah',
        help="Ayah number where memorization starts"
    )
    
    review_amount = fields.Text(
        string='Review Amount',
        help="Details about the review portion"
    )
    
    notes = fields.Text(
        string='Notes',
        help="Additional notes about the memorization session"
    )
    
    # Grade Fields
    student_grade = fields.Float(
        string='Student Grade',
        digits=(16, 1),
        help="Student's overall grade for memorization"
    )
    
    test_grade = fields.Integer(
        string='Test Grade',
        default=10,
        help="Student's test grade (must not exceed student grade)"
    )
    
    memorization_amount_juz = fields.Float(
        string='Memorization Amount (Juz\')',
        compute='_compute_memorization_amount_juz',
        inverse='_inverse_memorization_amount_juz',
        store=True,
        digits=(16, 2),
        help="Amount of Quran memorized in Juz' (parts) with decimal precision"
    )
    
    # Month and Date
    memorization_month = fields.Date(
        string='Memorization Month',
        required=True,
        default=lambda self: fields.Date.today(),
        help="Month and year for this memorization record"
    )
    
    month_name = fields.Char(
        string='Month Name',
        compute='_compute_month_name',
        store=True,
        readonly=True
    )

    # ========================= Built-in Functions =========================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence for memorization number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('student.memorization.number') or _('New')
        
        return super().create(vals_list)

    # ========================= OnChange Functions =========================

    @api.onchange('student_id')
    def _onchange_student_id(self):
        if self.student_id:
            self.office_id = self.student_id.office_id
            self.class_id = self.student_id.class_id
            self.teacher_id = self.student_id.teacher_id
            self.memorization_method = self.student_id.memorization_method

    @api.onchange('office_id')
    def _onchange_office_id(self):
        """
        Clear class_id and teacher_id when office changes to ensure proper filtering.
        """
        if (self.office_id and self.office_id != self.class_id.office_id) or not self.office_id:
            self.class_id = False

    @api.onchange('class_id')
    def _onchange_class_id(self):
        """
        Auto-fill teacher_id when class is selected.
        """
        if self.class_id:
            self.office_id = self.class_id.office_id
        if self.class_id and self.class_id.teacher_id:
            self.teacher_id = self.class_id.teacher_id

    @api.onchange('teacher_id')
    def _onchange_teacher_id(self):
        if self.teacher_id and not self.class_id:
            self.class_id = self.teacher_id.class_ids[0]

    @api.onchange('memorization_surah', 'memorization_ayah')
    def _onchange_memorization_surah_ayah(self):
        """
        Validate that ayah number is within the surah's ayat count.
        """
        if self.memorization_surah:
            if self.memorization_ayah < 1:
                self.memorization_ayah = 1
            elif self.memorization_ayah > self.memorization_surah.count_ayat:
                self.memorization_ayah = self.memorization_surah.count_ayat
        else:
            self.memorization_ayah = 0

    # ========================= constraints Functions =========================

    @api.constrains('memorization_month')
    def _check_future_month(self):
        """Check that memorization month is not in the future"""
        for record in self:
            if record.memorization_month:
                current_month = fields.Date.today()
                memorization_month = record.memorization_month
                if memorization_month > current_month:
                    raise ValidationError(_('Cannot create memorization record for future month %s') % record.month_name)

    @api.constrains('student_id')
    def _check_student_status(self):
        """Check student status before allowing memorization record"""
        for record in self:
            if record.student_id:
                # Check if student is disconnected.
                if record.student_id.student_status == 'disconnected':
                    raise ValidationError(
                        _('Cannot create memorization record for disconnected student %s. Please update student status first.') % record.student_id.name)

                # Check if student is active
                if not record.student_id.active:
                    raise ValidationError(
                        _('Cannot create memorization record for inactive student %s.') % record.student_id.name)

                if not record.student_id.is_student:
                    raise ValidationError(
                        _('Cannot create memorization record for non-student %s.') % record.student_id.name)

    @api.constrains('student_grade', 'test_grade')
    def _check_grades(self):
        """
        Constraint to ensure grades are not negative and test_grade doesn't exceed student_grade.
        """
        for record in self:
            # Check that student_grade is not negative
            if record.student_grade < 0:
                raise ValidationError(_('Student grade cannot be negative'))
            
            # Check that test_grade is not negative
            if record.test_grade < 0:
                raise ValidationError(_('Test grade cannot be negative'))
            
            # Check that test_grade doesn't exceed student_grade (only if student_grade is set)
            if record.student_grade > record.test_grade:
                raise ValidationError(_(
                    'Student grade (%d) cannot be greater than test grade (%.2f)'
                ) % (record.test_grade, record.student_grade))

    def _check_memorization_ayah(self):
        """
        Constraint to ensure ayah number is valid for the selected surah.
        """
        for record in self:
            if not (record.memorization_surah and record.memorization_ayah > 0):
                return False
            if record.memorization_ayah > record.memorization_surah.count_ayat:
                return False
            return True

    def _check_memorization_amount(self):
        for record in self:
            if record.memorization_amount_juz <= 0 or  record.memorization_amount_juz > 30:
                return False
            return True

    @api.constrains('memorization_amount_juz', 'memorization_method','memorization_surah', 'memorization_ayah')
    def _check_memorization_amount_consistency(self):
        """
        Validate memorization amount consistency with surah and ayah calculation.
        """
        for record in self:
            if record.memorization_method == 'mixed':
                if not self._check_memorization_amount() and not self._check_memorization_ayah():
                    raise ValidationError(_('Memorization amount or surah and ayah is required for mixed method'))
                continue

            if not self._check_memorization_amount() :
                raise ValidationError(_('Memorization amount must be greater than 0 and less than 30'))

    @api.constrains('student_id', 'memorization_month')
    def _check_unique_memorization_per_month(self):
        """Check that student doesn't have more than one memorization record per month"""
        for record in self:
            if record.student_id and record.memorization_month:
                # Check for existing memorization record for same student and month
                existing = self.search([
                    ('student_id', '=', record.student_id.id),
                    ('memorization_month', '=', record.memorization_month),
                    ('id', '!=', record.id),
                ])
                if existing:
                    raise ValidationError(_('Student %s already has a memorization record for %s') % (
                        record.student_id.name,
                        record.month_name or record.memorization_month.strftime('%B %Y')
                    ))

    # ========================= compute Functions =========================

    @api.depends('memorization_method', 'memorization_surah', 'memorization_ayah')
    def _compute_memorization_amount_juz(self):
        """
        Calculate memorization amount in Juz' (parts) based on memorization method and ayah position.
        Quran has 6236 ayahs total, divided into 30 Juz' (each Juz' ≈ 207.87 ayahs).
        """
        for record in self:
            if record.env.context.get('skip_compute_juz'):
                continue

            method = 2
            if record.memorization_method == 'from_baqarah':
                method = 1
            if record.memorization_method == 'from_nas':
                method = 0

            if not record.memorization_surah or record.memorization_ayah<=0:
                record.memorization_amount_juz = 0
            else:
                record.memorization_amount_juz = self.env['quran_office.ayat'].calc_memorization_amount_juz(method, record.memorization_surah.id, record.memorization_ayah)

    def _inverse_memorization_amount_juz(self):
        """ Calculate memorization surah and ayah based on memorization amount in Juz' """

        for record in self:
            method = 2
            if record.memorization_method == 'from_baqarah':
                method = 1
            if record.memorization_method == 'from_nas':
                method = 0

            result = self.env['quran_office.ayat'].calc_surah_ayah_from_amount(method, record.memorization_amount_juz)
            if result['surah_id'] == False or result['ayah_num'] == 0:
                continue
            record.with_context(skip_compute_juz=True).update({
                'memorization_surah': result['surah_id'],
                'memorization_ayah': result['ayah_num'],
            })
    
    @api.depends('memorization_month')
    def _compute_month_name(self):
        """Compute month name for display"""
        for record in self:
            if record.memorization_month:
                record.month_name = record.memorization_month.strftime('%B %Y')
            else:
                record.month_name = ''
    
    # ======================= Action Functions =======================
