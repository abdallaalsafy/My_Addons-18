# -*- coding: utf-8 -*-

import calendar
from datetime import date

from odoo import _, api, fields, models


class StudentMonthlyAbsenceSheetReport(models.AbstractModel):
    _name = 'report.management_quran_attendance.student_monthly_sheet'
    _description = 'Student Monthly Absence Sheet Report'

    _EN_MONTHS = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December',
    }

    _EN_WEEKDAYS = {
        0: 'Mo', 1: 'Tu', 2: 'We', 3: 'Th',
        4: 'Fr', 5: 'Sa', 6: 'Su',
    }

    @staticmethod
    def _month_label(month_number):
        return StudentMonthlyAbsenceSheetReport._EN_MONTHS.get(month_number, '')

    @staticmethod
    def _weekday_label(day_number, year, month):
        weekday = date(year, month, day_number).weekday()
        return StudentMonthlyAbsenceSheetReport._EN_WEEKDAYS.get(weekday, '')

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        students_ids = data.get('students_ids') or docids or []
        students = self.env['res.partner'].browse(students_ids)
        if not students:
            raise ValueError(_('No student selected for printing.'))

        report_date = fields.Date.from_string(data.get('report_date') or fields.Date.context_today(self))
        year = report_date.year
        month = report_date.month

        holiday_policy_id = data.get('holiday_policy_id')
        holiday_policy = holiday_policy_id and self.env['attendance.holiday.policy'].browse(int(holiday_policy_id)) or False

        office_id = data.get('office_id')
        office = office_id and self.env['quran.office.office'].browse(int(office_id)) or False

        teacher_id = data.get('teacher_id')
        teacher = teacher_id and self.env['res.partner'].browse(int(teacher_id)) or False

        holidays = holiday_policy._get_days_of_holiday_numbers(year, month)
        last_day = calendar.monthrange(year, month)[1]

        day_columns = []
        for day_number in range(1, last_day + 1):
            if day_number in holidays:
                continue
            day_columns.append({
                'day': day_number,
                'weekday': self._weekday_label(day_number, year, month),
            })

        rows = []
        for index, student in enumerate(students, 1):
            rows.append({
                'sequence': index,
                'code': student.ref or student.id,
                'name': student.name,
                'day_cells': [{'empty': True} for _ in day_columns],
            })

        return {
            'doc_model': 'res.partner',
            'docs': students,
            'report_date': report_date,
            'year': year,
            'month_name': self._month_label(month),
            'office_name': office.name if office else '',
            'teacher_name': teacher.name if teacher else '',
            'day_columns': day_columns,
            'students': rows,
            'status_hint': 'Note: P = Present, A = Absent, E = Excused, S = Sick, L = Late',
        }
