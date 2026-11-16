# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from datetime import date

class AttendanceBulkCreateWizard(models.TransientModel):
    _name = 'attendance.bulk.create.wizard'
    _inherit = ['school.organization.mixin']
    _description = 'Attendance Bulk Create Wizard'

    year = fields.Integer(
        string='Year',
        default=lambda self: fields.Date.context_today(self).year,
    )
    month = fields.Selection([
        ('1', '01'), ('2', '02'), ('3', '03'), ('4', '04'), ('5', '05'), ('6', '06'),
        ('7', '07'), ('8', '08'), ('9', '09'), ('10', '10'), ('11', '11'), ('12', '12')
    ], string='Month', required=True, default=lambda self: str(fields.Date.context_today(self).month))
    show_mode = fields.Selection([('by_date', 'Show all records with the same date'), ('by_ids', 'Show created records only')], string='Show Mode', default='by_ids',)
    create_mode = fields.Selection([('all', 'Create all of them, or create none of them'), ('any', 'Create all or a valid records only')], string='Create Mode', default='any',required=True)
    
    holiday_policy_id = fields.Many2one('attendance.holiday.policy', string='Holiday Policy',default=lambda self: self.env['attendance.register']._default_holiday_policy_record())

# ========================== Help Functions =============================
    def _get_valid_students(self):
        if self._context.get('active_model') not in (None, False, 'res.partner'):
            raise ValidationError(_('This wizard must be opened from the students list.'))
        ids = self._context.get('active_ids') or []
        all_students = self.env['res.partner'].browse(ids).exists()
        valid_students = all_students.filtered(lambda s: s.is_student)

        if not self.office_id:
            valid_students = valid_students.filtered(lambda s: s.office_id)

        # One query for all students instead of one query per student
        existing = self.env['attendance.register'].search([
            ('student_id', 'in', valid_students.ids),
            ('year', '=', self.year),
            ('month', '=', int(self.month)),
        ])
        existing_pairs = {(reg.student_id.id, reg.office_id.id) for reg in existing}
        has_attendance_students = valid_students.filtered(
            lambda s: (s.id, self.office_id.id or s.office_id.id) in existing_pairs)
        valid_students = valid_students - has_attendance_students
        return all_students, valid_students

# ========================= Action Function ===========================================
    def action_create_attendance_registers(self):
        self.ensure_one()
        if self.year == 0:
            raise ValidationError(_('Year and month are required.'))

        all_students, valid_students = self._get_valid_students()
        if not valid_students:
            raise ValidationError(_('No valid students match in the selected records.'))

        created_records = []
        for student in valid_students:
            created_records.append({
                'student_id': student.id,
                'office_id': self.office_id.id or student.office_id.id,
                'class_id': self.class_id.id or student.class_id.id or False,
                'teacher_id': self.teacher_id.id or student.teacher_id.id or False,
                'year': self.year,
                'month': int(self.month),
                'holiday_policy_id': self.holiday_policy_id.id or False,
            })

        if len(valid_students) != len(all_students) and self.create_mode == 'all':
            raise ValidationError(_('Some matched students are not valid, count: %s.') % (len(all_students) - len(valid_students)))
        
        context_date = fields.Date.to_string(date(self.year, int(self.month), 1))
        attendance_records = self.env['attendance.register'].with_context(default_date=context_date, create_lines_from_outside=True).create(created_records)
        domain = [('id', 'in', attendance_records.ids)] if self.show_mode == 'by_ids' else [('month', '=', self.month), ('year', '=', self.year)]
        view_id = self.env.ref('management_quran_attendance.view_attendance_register_list').id
        
        if not self.show_mode:
            return
        return {
            'name': _('Created Attendance Registers'),
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.register',
            'view_mode': 'list',
            'view_id': view_id,
            'domain': domain,
            'context': {'default_date':context_date},
        }