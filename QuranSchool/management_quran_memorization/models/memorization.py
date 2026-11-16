# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import format_date


class StudentMemorization(models.Model):
    _name = 'student.memorization'
    _inherit = ['memorization.mixin', 'school.organization.mixin']
    _description = 'Student Monthly Quran Memorization'
    _order = 'memorization_month desc, student_id'

    # Sequence Details
    name = fields.Char(
        string='Memorization Number',
        copy=False,
        readonly=True,
        default=lambda self: _('New')
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
    student_id = fields.Many2one(
        'res.partner', 
        string='Student Name',
        required=True,
        domain="[('is_student', '=', True)]"
    )
    office_id = fields.Many2one(ondelete='restrict')
    
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
        help="Student's overall grade for memorization",
    )
    test_grade = fields.Integer(
        string='Test Grade',
        default=10,
        help="Maximum grade of the test. The student grade cannot exceed it."
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

# ========================= compute Functions =========================
    @api.depends('memorization_month')
    @api.depends_context('lang')
    def _compute_month_name(self):
        """Compute month name for display"""
        for record in self:
            if record.memorization_month:
                record.month_name = format_date(self.env, record.memorization_month, date_format='MMMM yyyy')
            else:
                record.month_name = ''

# ========================= constraints Functions =========================
    @api.constrains('student_id', 'memorization_month', 'office_id')
    def _check_duplicate_memorization(self):
        """One memorization record per student, calendar month and office
        (compares real dates, also when the office is empty)."""
        for record in self:
            if not record.student_id or not record.memorization_month:
                continue
            month_start = record.memorization_month.replace(day=1)
            month_end = month_start + relativedelta(months=1)
            if self.search_count([
                ('student_id', '=', record.student_id.id),
                ('office_id', '=', record.office_id.id or False),
                ('memorization_month', '>=', month_start),
                ('memorization_month', '<', month_end),
                ('id', '!=', record.id),
            ]):
                raise ValidationError(_('Memorization must be unique per student per month per office.'))

    @api.constrains('memorization_month')
    def _check_future_month(self):
        """Check that memorization month is not in the future"""
        for record in self:
            if record.memorization_month:
                if record.memorization_month > fields.Date.today():
                    raise ValidationError(_('Cannot create memorization record for future month %s') % record.month_name)

    @api.constrains('student_id')
    def _check_student_status(self):
        """Check student status before allowing memorization record"""
        for record in self:
            if not record.student_id:
                raise ValidationError(_('Please select a student first.'))
            record.student_id.validate_status_of_student()

    @api.constrains('student_grade', 'test_grade')
    def _check_grades(self):
        """Grades are not negative and the student grade does not exceed the test (maximum) grade."""
        for record in self:
            # Check that student_grade is not negative
            if record.student_grade < 0:
                raise ValidationError(_('Student grade cannot be negative'))
            
            # Check that test_grade is not negative
            if record.test_grade < 0:
                raise ValidationError(_('Test grade cannot be negative'))
            
            # test_grade is the maximum grade: the student grade cannot exceed it
            if record.student_grade > record.test_grade:
                raise ValidationError(_(
                    'Student grade (%.1f) cannot be greater than test grade (%d)'
                ) % (record.student_grade, record.test_grade))

    @api.constrains('juze_amount', 'memorization_method','surah_id', 'surah_ids', 'ayah_num')
    def _constrains_memorization_amount_consistency(self):
        """Validate memorization amount consistency with surah and ayah calculation."""
        for record in self:
            if record.memorization_method != 'mixed':
                record._check_memorization_amount_consistency()
            else:
                record._constrain_memorization_amount()