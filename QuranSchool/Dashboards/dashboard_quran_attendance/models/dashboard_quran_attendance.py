# -*- coding: utf-8 -*-
from odoo import _, models

GROUP_USER = 'management_quran_office_core.group_quran_office_user'


class DashboardQuranAttendance(models.AbstractModel):
    """Dashboard data for management_quran_attendance.

    Source model ``attendance.register`` (one row per student per month; verified fields):
    date (first day of the month, stored), present_days (present + late), absent_days
    (absent + excused + sick), excused_days, sick_days, late_days, study_days
    (= present_days + absent_days), student_id, class_id, office_id.

    Rates only use days that were actually filled in (study_days), so partially filled months
    are not diluted by blank days. ``unrestricted`` and ``holiday`` days are not study days.
    """
    _name = 'dashboard.quran.attendance'
    _inherit = 'unified.dashboard.base'
    _description = 'Dashboard data: Quran Attendance'

    _ud_default_groups = (GROUP_USER,)

    def _ud_period_domain(self, period):
        return [
            ('date', '>=', period['month_from']),
            ('date', '<=', period['date_to']),
        ]

    def _ud_widget_attendance_kpis(self, period):
        Register = self.env['attendance.register']
        count, present, absent, excused, sick, late, study = Register._read_group(
            self._ud_period_domain(period), [],
            ['__count', 'present_days:sum', 'absent_days:sum', 'excused_days:sum',
             'sick_days:sum', 'late_days:sum', 'study_days:sum'])[0]
        if not count:
            return {'empty': True,
                    'empty_message': _("No attendance registers in the selected period.")}
        present, absent, excused, sick, late, study = (
            present or 0, absent or 0, excused or 0, sick or 0, late or 0, study or 0)
        return {'tiles': [
            {'label': _("Attendance rate"), 'value': self._ud_ratio(present, study),
             'format': 'percent', 'tone': 'good',
             'hint': _("Present or late, out of %s study days", study)},
            {'label': _("Absence rate"), 'value': self._ud_ratio(absent, study),
             'format': 'percent', 'tone': 'warn' if absent else 'good'},
            {'label': _("Unexcused absence days"), 'value': absent - excused - sick,
             'tone': 'warn' if absent - excused - sick else 'good'},
            {'label': _("Excused / sick days"), 'value': excused + sick, 'tone': 'neutral'},
            {'label': _("Late days"), 'value': late, 'tone': 'neutral'},
            {'label': _("Student registers"), 'value': count, 'tone': 'neutral',
             'hint': _("One per student per month")},
        ]}

    def _ud_widget_attendance_trend(self, period):
        months = self._ud_trend_months(period, 6)
        groups = self.env['attendance.register']._read_group(
            [('date', '>=', months[0]), ('date', '<=', period['date_to'])],
            ['date:month'],
            ['present_days:sum', 'study_days:sum'],
        )
        if not groups:
            return {'empty': True, 'empty_message': _("No attendance registers in the last 6 months.")}
        by_month = {m: self._ud_ratio(present or 0, study or 0) for m, present, study in groups}
        return {
            'format': 'percent',
            'title': _("Attendance rate per month"),
            'series': [{
                'name': _("Attendance rate"),
                'points': [{'label': self._ud_month_label(m), 'value': by_month.get(m)}
                           for m in months],
            }],
            'footer': _("Last 6 months ending at the period end. Based on filled-in study days only."),
        }

    def _ud_widget_attendance_classes(self, period):
        groups = self.env['attendance.register']._read_group(
            self._ud_period_domain(period), ['class_id'],
            ['absent_days:sum', 'study_days:sum'])
        rows = []
        for cls, absent, study in groups:
            rate = self._ud_ratio(absent or 0, study or 0)
            if rate is None:
                continue
            rows.append((rate, cls, absent or 0, study))
        if not rows:
            return {'empty': True, 'empty_message': _("No study days recorded in the selected period.")}
        rows.sort(key=lambda r: (-r[0], r[1].id or 0))
        items = [{
            'label': cls.display_name if cls else _("No class"),
            'value': rate,
            'secondary_text': _("%(absent)s absent days of %(study)s study days",
                                absent=absent, study=study),
        } for rate, cls, absent, study in rows[:10]]
        return {'format': 'percent', 'items': items}

    def _ud_widget_attendance_students(self, period):
        groups = self.env['attendance.register']._read_group(
            self._ud_period_domain(period), ['student_id'],
            ['absent_days:sum', 'study_days:sum'],
            having=[('absent_days:sum', '>', 0)],
            order='absent_days:sum desc', limit=10)
        if not groups:
            return {'empty': True, 'empty_message': _("No absences in the selected period.")}
        rows = [{
            'student': student.display_name,
            'absent': absent,
            'study': study,
            'rate': self._ud_ratio(absent or 0, study or 0),
            'drill': {'name': student.display_name, 'res_model': 'res.persons',
                      'res_id': student.id},
        } for student, absent, study in groups]
        return {
            'columns': [
                {'key': 'student', 'label': _("Student")},
                {'key': 'absent', 'label': _("Absent days"), 'format': 'integer', 'align': 'end'},
                {'key': 'study', 'label': _("Study days"), 'format': 'integer', 'align': 'end'},
                {'key': 'rate', 'label': _("Absence rate"), 'format': 'percent', 'align': 'end'},
            ],
            'rows': rows,
            'footer': _("Absent days include excused and sick days. Top 10 students."),
        }
