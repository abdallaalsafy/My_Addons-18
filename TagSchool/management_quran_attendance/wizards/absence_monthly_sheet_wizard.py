# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StudentMonthlyAbsenceSheetWizard(models.TransientModel):
    _name = 'student.monthly.absence.sheet.wizard'
    _description = 'Student Monthly Absence Sheet Wizard'

    report_date = fields.Date(
        string='Date',
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )

    holiday_policy_id = fields.Many2one(
        'attendance.holiday.policy',
        string='Absence Policy',
        required=True,
    )

    office_id = fields.Many2one(
        'quran.office.office',
        string='Office',
        required=True,
    )

    teacher_id = fields.Many2one(
        'res.partner',
        string='Teacher',
        domain="[('is_teacher', '=', True)]",
        required=True,
    )

    report_orientation = fields.Selection(
        [('portrait', 'Portrait'), ('landscape', 'Landscape')],
        string='Paper Orientation',
        default='landscape',
        required=True,
    )

    @api.constrains('report_date')
    def _check_report_date(self):
        for record in self:
            if record.report_date and record.report_date > fields.Date.context_today(record):
                raise ValidationError(_('The selected date cannot be greater than today.'))

    def action_print_report(self):
        self.ensure_one()

        active_ids = self._context.get('active_ids') or []
        students = self.env['res.partner'].browse(active_ids)

        invalid_students = students.filtered(lambda s: not s.is_student)
        if invalid_students:
            raise ValidationError(_('Please select students only.'))

        if not self.holiday_policy_id._validate_is_policy_valid(self.report_date.year, self.report_date.month):
            raise ValidationError(_('The selected holiday policy is not valid for the selected date.'))

        report_name = (
            'management_quran_attendance.action_report_student_monthly_absence_sheet_landscape'
            if self.report_orientation == 'landscape'
            else 'management_quran_attendance.action_report_student_monthly_absence_sheet_portrait'
        )
        report_action = self.env.ref(report_name)
        data = {
            'students_ids': students.ids,
            'report_date': self.report_date,
            'holiday_policy_id': self.holiday_policy_id.id,
            'office_id': self.office_id.id,
            'teacher_id': self.teacher_id.id,
        }
        return report_action.report_action(None, data=data)
