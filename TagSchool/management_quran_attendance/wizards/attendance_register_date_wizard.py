# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AttendanceRegisterDateWizard(models.TransientModel):
    _name = 'attendance.register.date.wizard'
    _description = 'Attendance Register Date Filter Wizard'

    date_from = fields.Date(
        string='From Date',
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )

    def action_show_records(self):
        self.ensure_one()

        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Start date cannot be greater than end date.'))

        return {
            'name': _('Attendance Register By Date Range'),
            'type': 'ir.actions.act_window',
            'res_model': 'attendance.register',
            'view_mode': 'list',
            'domain': [
                ('date', '>=', (self.date_from .strftime('%Y-%m-01'))),
                ('date', '<', (self.date_to + relativedelta(months=1)).strftime('%Y-%m-01')),
            ],
            'context': {
                'default_date': self.date_to,
                'group_by': ['date'],
            },
            'target': 'current',
        }
