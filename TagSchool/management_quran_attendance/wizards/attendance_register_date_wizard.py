# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AttendanceRegisterDateWizard(models.TransientModel):
    _name = 'attendance.register.date.wizard'
    _description = 'Attendance Register Date Filter Wizard'

    start_date = fields.Date(
            string='Start Date',
            required=True,
            default=lambda self: fields.Date.context_today(self),
        )
    end_date = fields.Date(
            string='End Date',
            required=True,
            default=lambda self: fields.Date.context_today(self),
        )

    office_id = fields.Many2one(
        'quran.office.office',
        string='Office',
    )

    def _validate_period(self):
            if not self.end_date or not self.start_date or self.end_date < self.start_date:
                raise ValidationError(_('The end date must be greater than or equal to the start date.'))
            
    def action_show_records(self):
        self.ensure_one()
        self._validate_period()

        domain = [
            ('date', '>=', (self.start_date .strftime('%Y-%m-01'))),
            ('date', '<', (self.end_date + relativedelta(months=1)).strftime('%Y-%m-01')),
        ]

        if self.office_id:            
            domain.append(('office_id', '=', self.office_id.id))

        return {
            'name': _('Attendance Register By Date Range'),
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.register',
            'view_mode': 'list',
            'domain': domain,
            'context': {
                'default_date': self.end_date,
                'group_by': ['date'],
            },
            'target': 'current',
        }

    def action_print_report(self):
        self.ensure_one()
        self._validate_period()

        ids = self._context.get('active_ids')
        students = self.env['res.partner'].browse(ids)
        is_not_students = students.filtered(lambda s: not s.is_student)

        if is_not_students:
            raise ValidationError(_('Please select students only.'))

        office_id = self.office_id.id or False

        report_action = self.env.ref('management_quran_attendance.action_report_student_attendance_detail')
        data = {
            'students_ids': students.ids,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'office_id': office_id,
        }
        
        return report_action.report_action(None, data=data)
