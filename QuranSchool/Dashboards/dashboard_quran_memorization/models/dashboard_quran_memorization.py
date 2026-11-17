# -*- coding: utf-8 -*-
from odoo import _, models

GROUP_USER = 'management_quran_office_core.group_quran_office_user'


class DashboardQuranMemorization(models.AbstractModel):
    """Dashboard data for management_quran_memorization.

    Source model ``student.memorization`` (verified fields): memorization_month (Date, any day of
    the month), student_grade (Float), test_grade (Integer, the maximum grade of that test),
    student_id, teacher_id, office_id.

    Grade policy: ``test_grade`` differs per record, so grades are reported as a weighted
    percentage = sum(student_grade) / sum(test_grade) over records with test_grade > 0.
    ``juze_amount`` is deliberately NOT aggregated per month: it is the student's cumulative
    position, not the amount memorized in that month.
    """
    _name = 'dashboard.quran.memorization'
    _inherit = 'unified.dashboard.base'
    _description = 'Dashboard data: Quran Memorization'

    _ud_default_groups = (GROUP_USER,)

    def _ud_period_domain(self, period):
        return [
            ('memorization_month', '>=', period['month_from']),
            ('memorization_month', '<=', period['date_to']),
        ]

    def _ud_widget_memorization_kpis(self, period):
        Memorization = self.env['student.memorization']
        domain = self._ud_period_domain(period)
        count, students = Memorization._read_group(
            domain, [], ['__count', 'student_id:count_distinct'])[0]
        graded = Memorization._read_group(
            domain + [('test_grade', '>', 0)], [],
            ['__count', 'student_grade:sum', 'test_grade:sum'])[0]
        graded_count, grade_sum, test_sum = graded[0] or 0, graded[1] or 0, graded[2] or 0
        grade_pct = self._ud_ratio(grade_sum, test_sum)

        # Eligible students (same rules as validate_student_for_memorization) with no record
        # in the month of the period end.
        month_start = period['date_to'].replace(day=1)
        recorded_ids = [
            student.id for (student,) in Memorization._read_group(
                [('memorization_month', '>=', month_start),
                 ('memorization_month', '<=', period['date_to'])],
                ['student_id'])
        ]
        missing_domain = [
            ('is_student', '=', True),
            ('status', '!=', 'disconnected'),
            ('office_id', '!=', False),
            ('id', 'not in', recorded_ids),
        ]
        missing = self.env['res.persons'].search_count(missing_domain)
        if not count and not missing:
            return {'empty': True,
                    'empty_message': _("No memorization records in the selected period.")}
        return {'tiles': [
            {'label': _("Memorization records"), 'value': count, 'tone': 'neutral'},
            {'label': _("Students followed"), 'value': students, 'tone': 'neutral'},
            {'label': _("Average grade"), 'value': grade_pct, 'format': 'percent',
             'tone': 'neutral',
             'hint': _("Weighted by each test's maximum grade (%s records)", graded_count)},
            {'label': _("Students without a record"), 'value': missing,
             'tone': 'warn' if missing else 'good',
             'hint': _("In %s", self._ud_month_label(month_start)),
             'drill': {'name': _("Students without a memorization record"),
                       'res_model': 'res.persons', 'domain': missing_domain} if missing else False},
        ]}

    def _ud_widget_memorization_trend(self, period):
        months = self._ud_trend_months(period, 6)
        groups = self.env['student.memorization']._read_group(
            [('memorization_month', '>=', months[0]),
             ('memorization_month', '<=', period['date_to']),
             ('test_grade', '>', 0)],
            ['memorization_month:month'],
            ['student_grade:sum', 'test_grade:sum'],
        )
        if not groups:
            return {'empty': True, 'empty_message': _("No graded records in the last 6 months.")}
        by_month = {m: self._ud_ratio(grade, test) for m, grade, test in groups}
        return {
            'format': 'percent',
            'title': _("Average grade per month"),
            'series': [{
                'name': _("Average grade"),
                'points': [{'label': self._ud_month_label(m), 'value': by_month.get(m)}
                           for m in months],
            }],
            'footer': _("Last 6 months ending at the period end, weighted by each test's maximum grade."),
        }

    def _ud_widget_memorization_by_teacher(self, period):
        Memorization = self.env['student.memorization']
        domain = self._ud_period_domain(period)
        counts = Memorization._read_group(
            domain, ['teacher_id'], ['__count'], order='__count desc', limit=10)
        if not counts:
            return {'empty': True, 'empty_message': _("No memorization records in the selected period.")}
        teacher_ids = [teacher.id for teacher, _count in counts if teacher]
        grade_domain = domain + [('test_grade', '>', 0)]
        # Only the teachers shown (plus "no teacher") are graded: one grouped query, no N+1.
        grade_domain += ['|', ('teacher_id', 'in', teacher_ids), ('teacher_id', '=', False)]
        pct_by_teacher = {
            teacher.id: self._ud_ratio(grade, test)
            for teacher, grade, test in Memorization._read_group(
                grade_domain, ['teacher_id'], ['student_grade:sum', 'test_grade:sum'])
        }
        items = []
        for teacher, count in counts:
            pct = pct_by_teacher.get(teacher.id if teacher else False)
            items.append({
                'label': teacher.display_name if teacher else _("No teacher"),
                'value': count,
                'secondary_text': (_("Average grade %s", f"{pct:.1f}%") if pct is not None
                                   else _("No graded records")),
            })
        return {'format': 'integer', 'items': items}
