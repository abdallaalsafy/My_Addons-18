from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class AttendanceHolidayDay(models.Model):
    _name = 'attendance.holiday.day'
    _description = 'Attendance Holiday Day'
    _order = 'holiday_date asc'

    policy_id = fields.Many2one('attendance.holiday.policy', string='Holiday Policy', ondelete='cascade', required=True)
    holiday_date = fields.Date(string='Holiday Date', required=True)
    year = fields.Integer(string='Year', compute='_compute_holiday_date_parts', store=True)
    month = fields.Integer(string='Month', compute='_compute_holiday_date_parts', store=True)
    day_number = fields.Integer(string='Day Number', compute='_compute_holiday_date_parts', store=True)
    day_name = fields.Char(string='Day Name', compute='_compute_holiday_date_parts', store=True, translate=True)
    reason = fields.Char(string='Reason')

    _sql_constraints = [
        (
            'unique_policy_date',
            'unique(policy_id, holiday_date)',
            'This date is already marked as a holiday in this policy.'
        )
    ]

    # ========== Compute Methods ==============================================

    @api.depends('holiday_date')
    def _compute_holiday_date_parts(self):
        for rec in self:
            if rec.holiday_date:
                rec.year = rec.holiday_date.year
                rec.month = rec.holiday_date.month
                rec.day_number = rec.holiday_date.day
                rec.day_name = rec.holiday_date.strftime('%A')
            else:
                rec.year = 0
                rec.month = 0
                rec.day_number = 0
                rec.day_name = ''

    # ========== Constraints Methods =============================
    @api.constrains('policy_id', 'holiday_date',)
    def _check_valid_holiday_date(self):
        for rec in self:
            if not rec.policy_id or not rec.holiday_date:
                raise ValidationError(_('Both policy and holiday date must be set.'))
            
    # ========== Onchange Methods =============================

