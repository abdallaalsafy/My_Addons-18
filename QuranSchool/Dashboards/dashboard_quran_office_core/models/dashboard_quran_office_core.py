# -*- coding: utf-8 -*-
from odoo import _, models

GROUP_USER = 'management_quran_office_core.group_quran_office_user'


class DashboardQuranOffice(models.AbstractModel):
    """Dashboard data for management_quran_office_core (students, teachers, offices, classes).

    Source models/fields (all verified in management_quran_office_core / quran_utils):
      res.persons: is_student, is_teacher, status, is_fatherless, office_id, class_id,
                   teacher_id, class_ids, active, juze_amount, memorization_method
      quran.office.office, quran.office.class (teacher_id, active)
    These widgets are snapshots of the current state and ignore the period filter.
    """
    _name = 'dashboard.quran.office'
    _inherit = 'unified.dashboard.base'
    _description = 'Dashboard data: Quran Office Core'

    _ud_default_groups = (GROUP_USER,)

    # Memorization bands (Juz'), upper bound inclusive. juze_amount is a stored computed
    # float; "mixed" students have no computed amount and are reported separately.
    _JUZ_BANDS = ((0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30))

    # ------------------------------------------------------------------ helpers
    def _ud_students_domain(self, extra=None):
        return [('is_student', '=', True)] + (extra or [])

    def _ud_drill(self, name, model, domain):
        return {'name': name, 'res_model': model, 'domain': domain}

    # ------------------------------------------------------------------ widgets
    def _ud_widget_students_overview(self, period):
        Persons = self.env['res.persons']
        status_counts = {
            status: count
            for status, count in Persons._read_group(
                self._ud_students_domain(), ['status'], ['__count'])
        }
        students = sum(status_counts.values())
        teachers = Persons.search_count([('is_teacher', '=', True)])
        offices = self.env['quran.office.office'].search_count([])
        classes = self.env['quran.office.class'].search_count([])
        if not (students or teachers or offices or classes):
            return {'empty': True, 'empty_message': _("No students, teachers, offices or classes yet.")}
        fatherless = Persons.search_count(self._ud_students_domain([('is_fatherless', '=', True)]))
        students_domain = self._ud_students_domain()
        return {'tiles': [
            {'label': _("Active students"), 'value': students, 'tone': 'neutral',
             'drill': self._ud_drill(_("Students"), 'res.persons', students_domain)},
            {'label': _("Persistent"), 'value': status_counts.get('persistent', 0), 'tone': 'good',
             'drill': self._ud_drill(_("Persistent students"), 'res.persons',
                                     self._ud_students_domain([('status', '=', 'persistent')]))},
            {'label': _("Disconnected"), 'value': status_counts.get('disconnected', 0), 'tone': 'warn',
             'drill': self._ud_drill(_("Disconnected students"), 'res.persons',
                                     self._ud_students_domain([('status', '=', 'disconnected')]))},
            {'label': _("Teachers"), 'value': teachers, 'tone': 'neutral',
             'drill': self._ud_drill(_("Teachers"), 'res.persons', [('is_teacher', '=', True)])},
            {'label': _("Offices"), 'value': offices, 'tone': 'neutral'},
            {'label': _("Classes"), 'value': classes, 'tone': 'neutral'},
            {'label': _("Fatherless students"), 'value': fatherless, 'tone': 'neutral',
             'drill': self._ud_drill(_("Fatherless students"), 'res.persons',
                                     self._ud_students_domain([('is_fatherless', '=', True)]))},
        ]}

    def _ud_widget_students_by_office(self, period):
        groups = self.env['res.persons']._read_group(
            self._ud_students_domain(), ['office_id'], ['__count'], order='__count desc')
        if not groups:
            return {'empty': True, 'empty_message': _("No students yet.")}
        top, others = groups[:10], groups[10:]
        items = []
        for office, count in top:
            if office:
                label = office.display_name
                drill = self._ud_drill(label, 'res.persons',
                                       self._ud_students_domain([('office_id', '=', office.id)]))
            else:
                label = _("No office")
                drill = self._ud_drill(label, 'res.persons',
                                       self._ud_students_domain([('office_id', '=', False)]))
            items.append({'label': label, 'value': count, 'drill': drill})
        if others:
            items.append({
                'label': _("Other offices (%s)", len(others)),
                'value': sum(count for _office, count in others),
            })
        return {'format': 'integer', 'items': items}

    def _ud_widget_students_levels(self, period):
        Persons = self.env['res.persons']
        base = self._ud_students_domain()
        total = Persons.search_count(base)
        if not total:
            return {'empty': True, 'empty_message': _("No students yet.")}
        not_mixed = base + [('memorization_method', '!=', 'mixed')]
        items = [{
            'label': _("No memorization recorded"),
            'value': Persons.search_count(not_mixed + [('juze_amount', '<=', 0)]),
        }]
        for low, high in self._JUZ_BANDS:
            items.append({
                'label': _("%(low)s – %(high)s Juz'", low=low, high=high),
                'value': Persons.search_count(
                    not_mixed + [('juze_amount', '>', low), ('juze_amount', '<=', high)]),
            })
        mixed = Persons.search_count(base + [('memorization_method', '=', 'mixed')])
        if mixed:
            items.append({'label': _("Mixed method (by Surahs)"), 'value': mixed})
        return {'format': 'integer', 'items': items}

    def _ud_widget_data_gaps(self, period):
        Persons = self.env['res.persons']
        checks = [
            (_("Students without an office"), 'res.persons',
             self._ud_students_domain([('office_id', '=', False)])),
            (_("Students without a class"), 'res.persons',
             self._ud_students_domain([('class_id', '=', False)])),
            (_("Students without a teacher"), 'res.persons',
             self._ud_students_domain([('teacher_id', '=', False)])),
            (_("Students without a status"), 'res.persons',
             self._ud_students_domain([('status', '=', False)])),
            (_("Classes without a teacher"), 'quran.office.class', [('teacher_id', '=', False)]),
            (_("Teachers without a class"), 'res.persons',
             [('is_teacher', '=', True), ('class_ids', '=', False)]),
        ]
        tiles = []
        for label, model, domain in checks:
            count = self.env[model].search_count(domain)
            tiles.append({
                'label': label,
                'value': count,
                'tone': 'warn' if count else 'good',
                'drill': self._ud_drill(label, model, domain) if count else False,
            })
        return {'tiles': tiles}
