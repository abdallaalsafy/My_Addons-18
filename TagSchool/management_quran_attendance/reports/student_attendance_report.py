# -*- coding: utf-8 -*-

import calendar

from odoo import _, api, fields, models
from datetime import date

class StudentAttendanceReport(models.AbstractModel):
    _name = 'report.management_quran_attendance.student_attendance_detail'
    _description = 'Student Attendance Detail Report'

    @staticmethod
    def _status_label(status):
        labels = {
            'present': 'P',
            'absent': 'A',
            'holiday': 'H',
            'excused': 'E',
            'sick': 'S',
            'late': 'L',
            'unrestricted': 'Un',
        }
        return labels.get(status, '')

    @staticmethod
    def _status_css(status):
        css_map = {
            'present': 'bg-success text-white',
            'absent': 'bg-danger text-white',
            'holiday': 'bg-info text-white',
            'excused': 'bg-warning text-dark',
            'sick': 'bg-secondary text-white',
            'late': 'bg-primary text-white',
            'unrestricted': 'bg-light text-dark',
        }
        return css_map.get(status, 'bg-light text-dark')

    @api.model
    def _get_month_report_data(self, students, year, month, office_id):
        today = fields.Date.context_today(self)
        last_day = today.day if month == today.month and year == today.year else calendar.monthrange(year, month)[1]
        
        domain = [
            ('student_id', 'in', students.ids),
            ('year', '=', year),
            ('month', '=', month),
        ]
        if office_id:
            domain.append(('office_id', '=', office_id))

        office_groups = {}
        registers = self.env['attendance.register'].search(domain, order='office_id,student_id')

        for register in registers:
            student = register.student_id
            class_id = register.class_id
            teacher_id = register.teacher_id
            office = register.office_id
            office_key = office.id
            office_groups.setdefault(office_key, {'office': office, 'students': []})

            day_rows = []
            for day_number in range(1, last_day + 1):
                value = getattr(register, f'day_{day_number}', False)
                day_rows.append({
                    'day': day_number,
                    'status': self._status_label(value),
                    'css_class': self._status_css(value),
                })

            student_data = {
                'name': student.name,
                'office': office.name,
                'class': class_id.name if class_id else '-',
                'teacher': teacher_id.name if teacher_id else '-',
                'present': register.present_days,
                'absent': register.absent_days,
                'holiday': register.holiday_days,
                'excused': register.excused_days,
                'sick': register.sick_days,
                'late': register.late_days,
                'study_days': register.study_days,
                'day_rows': day_rows,
            }
            office_groups[office_key]['students'].append(student_data)

        return {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'last_day': last_day,
            'groups': office_groups,
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        students_ids = list(data.get('students_ids'))
        students = self.env['res.partner'].browse(students_ids)
        start_date = fields.Date.from_string(data.get('start_date'))
        end_date = fields.Date.from_string(data.get('end_date'))
        office_id = int(data.get('office_id'))
        date_period = {'start_date': calendar.month_name[start_date.month] + " " + str(start_date.year), 'end_date': calendar.month_name[end_date.month] + " " + str(end_date.year)}

        periods = []
        current = start_date.replace(day=1)

        while current <= end_date:
            period = self._get_month_report_data(students, current.year, current.month, office_id)
            if period['groups']:
                periods.append(period)
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)
  
        return {
            'doc_model': 'res.partner',
            'docs': students,
            'periods': periods,
            'date_period': date_period,
            'total_students': len(students),
        }
