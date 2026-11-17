# -*- coding: utf-8 -*-

from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class ResPersons(models.Model):
    _inherit = 'res.persons'


    attend_status = fields.Selection([('attend', 'Attended'),('non_attend', 'Non-Attended'),], 
        string='Attendance Status',
        help="Previous attendance status for this student (only shown for students)",
        compute='_compute_student_attendance_status',
    )
    attendance_register_ids = fields.One2many(
        'attendance.register',
        'student_id',
        string='Attendance Registers',
    )
    # Attendance count for students
    attendance_count = fields.Integer(
        'Attendance Count',
        compute='_compute_attendance_count',
        help="Number of attendances for this student (only shown for students)"
    )
    # Is not used yet, but can be used to show if the student has attendance for the current day
    attendance_current_day = fields.Boolean(compute='_compute_attendance_current_day',)


    def _compute_student_attendance_status(self):
        """
            Determine the student's attendance status based on current month attendance and previous month attendance.

            - If a monthly attendance record exists and the student has no attendance
            days marked as present, the student is considered non-attended.
            - If at least one attendance day is marked as present, the student is
            considered attended.
            - If no monthly attendance record exists for the previous and current month, the
            student's attendance status remains non-attended.
            """
        today = fields.Date.today()
        
        for record in self:
            attendance_register_ids = record.attendance_register_ids
            if not record.is_student or not attendance_register_ids:
                record.attend_status = 'non_attend'
                continue

            previous_month = today - relativedelta(months=1)
            recent_registers = attendance_register_ids.filtered_domain([
                '|','&',
                ('year', '=', previous_month.year),
                ('month', '=', previous_month.month),
                '&',
                ('year', '=', today.year),
                ('month', '=', today.month)
            ])
            
            if not recent_registers:
                record.attend_status = 'non_attend'
                continue

            has_recent_attendance = False
            for register in recent_registers:
                if register.present_days > 0:
                    has_recent_attendance = True
                    break

            record.attend_status = 'attend' if has_recent_attendance else 'non_attend'

    def _compute_attendance_count(self):
        """
        Compute the number of attendances for this student (only for students)
        """
        for record in self:
            if record.is_student:
                # Count attendances where this person is the student
                record.attendance_count = len(record.attendance_register_ids)
            else:
                record.attendance_count = 0

    def _compute_attendance_current_day(self):
        """
        Compute the current day attendance for this student (only for students)
        """
        for record in self:
            if not record.is_student:
                record.attendance_current_day = False
                continue

            today = fields.Date.today()
            # Count attendances where this person is the student
            registers = record.attendance_register_ids.filtered(
                lambda r: r.year == today.year and r.month == today.month and r.office_id == record.office_id
            )

            if not registers:
                record.attendance_current_day = False
                continue

            for register in registers:
                if register[f'day_{today.day}'] != False:
                    record.attendance_current_day = True
                    break
                else:
                    record.attendance_current_day = False

    def _mark_student_current_month_attendance(self, status):
        """
        Set status of the current month's attendance record for selected students.
        """
        today = fields.Date.today()

        for record in self:
            register = record.attendance_register_ids.filtered(
                lambda r: r.year == today.year and r.month == today.month
            )

            if len(register) == 0:
                raise ValidationError(_('No attendance register found for this student: %s') % record.name)
            elif len(register) > 1:
                register = record.attendance_register_ids.filtered(
                        lambda r: r.year == today.year and r.month == today.month and r.office_id == record.office_id
                )
                if len(register) == 0:
                    raise ValidationError(_('There is more than one attendance register for this student: %s , and office: %s does not match') % (record.name, record.office_id.name))

            for day in range(1, today.day):
                if register[f'day_{day}'] == False:
                    raise ValidationError(_('Attendance register for this student: %s , has previous attendance for day: %s , it is not filled') % (record.name, day))
            
            if register[f'day_{today.day}'] == 'holiday':
                raise ValidationError(_('Attendance register for this student: %s , the today is a holiday')% (record.name))
            
            register.write({f'day_{today.day}': status})

    def action_mark_present_today(self):
        """Override the default persistent action to record attendance in the current month."""
        self._mark_student_current_month_attendance('present')


    def action_mark_absent_today(self):
        """Override the default disconnected action to record absence for the current month."""
        self._mark_student_current_month_attendance('absent')

    def action_view_attendance(self):
        """View attendances of this student"""
        self.ensure_one()
        name = _('Attendances of %s') % self.name
        domain = [('student_id', '=', self.id)]
        
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.register',
            'view_mode': 'list,form',
            'domain': domain,
            'context': { 'default_student_id': self.id, }
        }


