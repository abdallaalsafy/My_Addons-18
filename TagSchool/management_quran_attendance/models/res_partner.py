# -*- coding: utf-8 -*-

import calendar
from datetime import date, timedelta

from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    student_status = fields.Selection(compute='_compute_student_status',store=True, default=False,
        help='A student is considered persistent if they have at least one present attendance record within the last 31 days.',
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
    attendance_current_day = fields.Boolean(compute='_compute_attendance_current_day',)


    @api.depends('is_student', 'attendance_register_ids.present_days',)
    def _compute_student_status(self):
        """ 
        Compute the student status based on the number of present days.
        If the student has more than 0 present days in the last 31 days or this month and last month, the status is 'present'.
         Otherwise, the status is 'absent'.
        """
        today = fields.Date.today()
        
        for record in self:
            if not record.is_student:
                record.student_status = False
                continue

            recent_registers = record.attendance_register_ids.filtered(
                            lambda r: r.year and r.month and (
                                (today - date(r.date.year, r.date.month, today.day)).days <= 31
                            )
                        )
            
            if not recent_registers:
                record.student_status = 'disconnected'
                continue

            has_recent_attendance = False
            for register in recent_registers:
                if register.present_days > 0:
                    has_recent_attendance = True
                    break

            record.student_status = 'persistent' if has_recent_attendance else 'disconnected'

    def _compute_attendance_count(self):
        """
        Compute the number of attendances for this student (only for students)
        """
        for record in self:
            if record.is_student:
                # Count attendances where this partner is the student
                record.attendance_count = len(record.attendance_register_ids)
            else:
                record.attendance_count = 0

    def _compute_attendance_current_day(self):
        """
        Compute the current day attendance for this student (only for students)
        """
        for record in self:
            if not record.is_student:
                continue

            today = fields.Date.context_today(self)
            # Count attendances where this partner is the student
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
        today = fields.Date.context_today(self)

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
            
            if register[f'day_{today.day}' == 'holiday']:
                raise ValidationError(_('Attendance register for this student: %s , the today is a holiday')% (record.name))
            
            register.write({f'day_{today.day}': status})

    def action_mark_persistent(self):
        """Override the default persistent action to record attendance in the current month."""
        self._mark_student_current_month_attendance('present')


    def action_mark_disconnected(self):
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


