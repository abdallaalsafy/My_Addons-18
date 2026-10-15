# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class BatchMemorizationWizard(models.TransientModel):
    _name = 'batch.memorization.wizard'
    _description = 'Batch Student Memorization Registration Wizard'

    memorization_month = fields.Date(
        string='Memorization Month',
        required=True,
        default=lambda self: fields.Date.today(),
        help="Month and year for this memorization batch"
    )
    
    month_name = fields.Char(
        string='Month Name',
        compute='_compute_month_name',
        readonly=True
    )
    
    office_id = fields.Many2one(
        'quran_office.office',
        string='Office',
        help="Select office to filter students"
    )
    
    class_id = fields.Many2one(
        'quran_office.class',
        string='Class',
        domain="[('office_id', '=?', office_id)]",
        help="Select class to filter students"
    )
    
    teacher_id = fields.Many2one(
        'res.partner',
        string='Teacher',
        domain="[('is_teacher', '=', True)]",
        help="Teacher for the memorization batch"
    )
    
    memorization_method = fields.Selection([
        ('from_baqarah', 'Memorization from Al-Baqarah'),
        ('from_nas', 'Memorization from An-Nas'),
        ('mixed', 'Mixed Memorization'),
    ], 
    string='Memorization Method',
    required=True,
    default='from_baqarah',
    help="Method of Quran memorization for this batch"
    )
    
    memorization_surah = fields.Many2one(
        'quran_office.surah',
        string='Memorization Surah',
        help="Surah where memorization starts for this batch"
    )
    
    memorization_ayah = fields.Integer(
        string='Memorization Ayah',
        help="Ayah number where memorization starts for this batch"
    )

    # ================================= Dependencies Functions =================================
    @api.depends('memorization_month')
    def _compute_month_name(self):
        """Compute month name for display"""
        for record in self:
            if record.memorization_month:
                record.month_name = record.memorization_month.strftime('%B %Y')
            else:
                record.month_name = ''

    # ================================= Onchange Functions =================================
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

    # ========================= Action Functions =========================
    def action_register_memorization(self):
        """Register memorization for selected students"""
        self.ensure_one()

        # Get active students
        active_ids = self._context.get('active_ids')
        all_active_students = self.env['res.partner'].browse(active_ids)
        
        if not all_active_students:
            raise UserError(_('Please select at least one student to register memorization.'))
        
        # Validate ayah exists in surah
        if self.memorization_ayah < 1 or self.memorization_ayah > self.memorization_surah.count_ayat:
            raise UserError(_('Ayah number %d is not valid for Surah %s. Valid range: 1-%d.') % (
                self.memorization_ayah, self.memorization_surah.name, self.memorization_surah.count_ayat))
        
        memorization_vals_list = []
        
        for student in all_active_students:
            # Check if student already has memorization for this month
            # existing_memorization = self.env['student.memorization'].search([
            #     ('student_id', '=', student.id),
            #     ('memorization_month', '=', self.memorization_month)
            # ])
            #
            # if existing_memorization:
            #     # Skip students who already have memorization for this month
            #     continue
            #
            # # Calculate memorization amount
            # method = 2
            # if self.memorization_method == 'from_baqarah':
            #     method = 1
            # elif self.memorization_method == 'from_nas':
            #     method = 0
            #
            # memorization_amount = self.env['quran_office.ayat'].calc_memorization_amount_juz(
            #     method, self.memorization_surah.id, self.memorization_ayah
            # )
            
            memorization_vals = {
                'student_id': student.id,
                'office_id': self.office_id.id,
                'class_id': self.class_id.id,
                'teacher_id': self.teacher_id.id,
                'memorization_month': self.memorization_month,
                'memorization_method': self.memorization_method,
                'memorization_surah': self.memorization_surah.id,
                'memorization_ayah': self.memorization_ayah,
                # 'memorization_amount_juz': memorization_amount,
            }
            
            memorization_vals_list.append(memorization_vals)
        
        if memorization_vals_list:
            # Create memorization records
             self.env['student.memorization'].create(memorization_vals_list)