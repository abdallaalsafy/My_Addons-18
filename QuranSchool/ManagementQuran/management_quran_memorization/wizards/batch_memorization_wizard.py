# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools import format_date


class BatchMemorizationWizard(models.TransientModel):
    _name = 'batch.memorization.wizard'
    _inherit = ['memorization.mixin', 'school.organization.mixin']
    _description = 'Batch Student Memorization Registration Wizard'

    def _get_defaults_values(self):
        """Get default values for the wizard fields based on the context."""
        defaults = {}
        active_ids = self._context.get('active_ids', [])
        if len(active_ids) == 1:
            students = self.env['res.persons'].browse(active_ids)
            if len(students) == 1:
                student = students[0]
                defaults['office_id'] = student.office_id
                defaults['class_id'] = student.class_id
                defaults['teacher_id'] = student.teacher_id
        return defaults

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
    office_id = fields.Many2one(default=lambda self: self._get_defaults_values().get('office_id'))
    class_id = fields.Many2one(default=lambda self: self._get_defaults_values().get('class_id'))
    teacher_id = fields.Many2one(default=lambda self: self._get_defaults_values().get('teacher_id'),)

# ================================= Dependencies Functions =================================
    @api.depends('memorization_month')
    @api.depends_context('lang')
    def _compute_month_name(self):
        """Compute month name for display"""
        for record in self:
            if record.memorization_month:
                record.month_name = format_date(self.env, record.memorization_month, date_format='MMMM yyyy')
            else:
                record.month_name = ''
                
# ============================ Constraint Functions =========================
    @api.constrains('juze_amount', 'memorization_method','surah_id', 'surah_ids', 'ayah_num')
    def _constrains_memorization_amount_consistency(self):
        """Validate memorization amount consistency with surah and ayah calculation."""
        for record in self:
            if record.memorization_method != 'mixed':
                record._check_memorization_amount_consistency()
            else:
                record._constrain_memorization_amount()

# ========================= Action Functions =========================
    def action_register_memorization(self):
        """Register memorization for all eligible students"""
        if self._context.get('active_model') not in (None, False, 'res.persons'):
            raise ValidationError(_('This wizard must be opened from the students list.'))
        students = self.env['res.persons'].browse(self._context.get('active_ids') or []).exists()

        memorization_vals_list = []
        for student in students:
            memorization_month = self.memorization_month
            office_id = self.office_id or student.office_id
            class_id = self.class_id or student.class_id
            teacher = self.teacher_id or student.teacher_id
            student.validate_student_for_memorization(month=memorization_month, office=office_id)

            memorization_vals_list.append({
                'student_id': student.id,
                'office_id': office_id.id,
                'class_id': class_id.id,
                'teacher_id': teacher.id,
                'memorization_month': memorization_month,
                'memorization_method': self.memorization_method,
                'surah_id': self.surah_id.id,
                'ayah_num': self.ayah_num,
                'surah_ids': [(6, 0, self.surah_ids.ids)],
                'juze_amount': self.juze_amount,
            })

        self.env['student.memorization'].create(memorization_vals_list)