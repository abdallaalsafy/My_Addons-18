# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class BatchMemorizationWizard(models.TransientModel):
    _name = 'batch.memorization.wizard'
    _inherit = ['memorization.mixin']
    _description = 'Batch Student Memorization Registration Wizard'

    def _get_defaults_values(self):
        """Get default values for the wizard fields based on the context."""
        defaults = {}
        active_ids = self._context.get('active_ids', [])
        if len(active_ids) == 1:
            students = self.env['res.partner'].browse(active_ids)
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
    office_id = fields.Many2one(
        'quran.office.office',
        string='Office',
        default=lambda self: self._get_defaults_values().get('office_id'),
        help="Select office to filter students"
    )
    class_id = fields.Many2one(
        'quran.office.class',
        string='Class',
        domain="[('office_id', '=?', office_id)]",
        default=lambda self: self._get_defaults_values().get('class_id'),
        help="Select class to filter students"
    )
    teacher_id = fields.Many2one(
        'res.partner',
        string='Teacher',
        domain="[('is_teacher', '=', True)]",
        default=lambda self: self._get_defaults_values().get('teacher_id'),
        help="Teacher for the memorization batch"
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
        """Clear class_id and teacher_id when office changes to ensure proper filtering."""
        if (self.office_id and self.office_id != self.class_id.office_id) or not self.office_id:
            self.class_id = False

    @api.onchange('class_id')
    def _onchange_class_id(self):
        """Auto-fill teacher_id when class is selected."""
        if self.class_id:
            self.office_id = self.class_id.office_id
        if self.class_id and self.class_id.teacher_id:
            self.teacher_id = self.class_id.teacher_id

    @api.onchange('teacher_id')
    def _onchange_teacher_id(self):
        if self.teacher_id and not self.class_id:
            self.class_id = self.teacher_id.class_ids[0]

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
        active_ids= self._context.get('active_ids')
        students = self.env['res.partner'].browse(active_ids)

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