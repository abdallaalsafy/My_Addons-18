import calendar
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttendanceRegister(models.Model):
    _name = 'attendance.register'
    _description = 'Attendance Register'

    _ATTENDANCE_STATUS = [
        ('present', 'Present'),
        ('absent', 'Absent')
    ]

    student_id = fields.Many2one('res.partner', string='Students', domain="[('is_student', '=', True)]", required=True)
    date = fields.Date(string='Date')
    year = fields.Integer(string='Year')
    month = fields.Integer(string='Month')
    holiday_policy_id = fields.Many2one('attendance.holiday.policy', string='Holiday Policy', readonly=True)
    is_leap_year = fields.Boolean(string='Is Leap Year', compute='_compute_is_leap_year', store=False)
    day_1 = fields.Boolean(default=lambda self: self._default_day_value(), string='01')
    day_2 = fields.Boolean(default=lambda self: self._default_day_value(), string='02')
    day_3 = fields.Boolean(default=lambda self: self._default_day_value(), string='03')
    day_4 = fields.Boolean(default=lambda self: self._default_day_value(), string='04')
    day_5 = fields.Boolean(default=lambda self: self._default_day_value(), string='05')
    day_6 = fields.Boolean(default=lambda self: self._default_day_value(), string='06')
    day_7 = fields.Boolean(default=lambda self: self._default_day_value(), string='07')
    day_8 = fields.Boolean(default=lambda self: self._default_day_value(), string='08')
    day_9 = fields.Boolean(default=lambda self: self._default_day_value(), string='09')
    day_10 = fields.Boolean(default=lambda self: self._default_day_value(), string='10')
    day_11 = fields.Boolean(default=lambda self: self._default_day_value(), string='11')
    day_12 = fields.Boolean(default=lambda self: self._default_day_value(), string='12')
    day_13 = fields.Boolean(default=lambda self: self._default_day_value(), string='13')
    day_14 = fields.Boolean(default=lambda self: self._default_day_value(), string='14')
    day_15 = fields.Boolean(default=lambda self: self._default_day_value(), string='15')
    day_16 = fields.Boolean(default=lambda self: self._default_day_value(), string='16')
    day_17 = fields.Boolean(default=lambda self: self._default_day_value(), string='17')
    day_18 = fields.Boolean(default=lambda self: self._default_day_value(), string='18')
    day_19 = fields.Boolean(default=lambda self: self._default_day_value(), string='19')
    day_20 = fields.Boolean(default=lambda self: self._default_day_value(), string='20')
    day_21 = fields.Boolean(default=lambda self: self._default_day_value(), string='21')
    day_22 = fields.Boolean(default=lambda self: self._default_day_value(), string='22')
    day_23 = fields.Boolean(default=lambda self: self._default_day_value(), string='23')
    day_24 = fields.Boolean(default=lambda self: self._default_day_value(), string='24')
    day_25 = fields.Boolean(default=lambda self: self._default_day_value(), string='25')
    day_26 = fields.Boolean(default=lambda self: self._default_day_value(), string='26')
    day_27 = fields.Boolean(default=lambda self: self._default_day_value(), string='27')
    day_28 = fields.Boolean(default=lambda self: self._default_day_value(), string='28')
    day_29 = fields.Boolean(default=lambda self: self._default_day_value(), string='29')
    day_30 = fields.Boolean(default=lambda self: self._default_day_value(), string='30')
    day_31 = fields.Boolean(default=lambda self: self._default_day_value(), string='31')

    @api.model
    def _default_day_value(self):
        return bool(self.env['ir.config_parameter'].sudo().get_param('attendance_register.auto_day_value', default=True))

    def _ensure_holiday_policy_for_year(self, year, month):
        if not year or not month:
            return False, False

        policy = self.env['attendance.holiday.policy'].ensure_for_year(year)
        if not policy:
            return False, False

        holiday_month = self.env['attendance.month.holiday'].search([
            ('policy_id', '=', policy.id),
            ('year', '=', int(year)),
            ('month', '=', int(month)),
        ], limit=1)
        return policy, holiday_month

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            year = vals.get('year')
            month = vals.get('month')
            self._validate_year_month(year, month)
            if year and month:
                policy, holiday_month = self._ensure_holiday_policy_for_year(year, month)
                vals['holiday_policy_id'] = policy and policy.id or False
                vals['holiday_month_id'] = holiday_month and holiday_month.id or False
                vals['date'] = fields.Date.to_string(date(int(year), int(month), 1))
            vals = self._reset_invalid_day_fields(vals)
        return super().create(vals_list)

    def write(self, vals):
        if 'year' in vals or 'month' in vals:
            year = vals.get('year', self.year)
            month = vals.get('month', self.month)
            self._validate_year_month(year, month)
            vals['year'] = year
            vals['month'] = month
            if year and month:
                policy, holiday_month = self._ensure_holiday_policy_for_year(year, month)
                vals['holiday_policy_id'] = policy and policy.id or False
                vals['holiday_month_id'] = holiday_month and holiday_month.id or False
                vals['date'] = fields.Date.to_string(date(int(year), int(month), 1))

        vals = self._reset_invalid_day_fields(vals)
        return super().write(vals)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        default_date = self.env.context.get('default_date')

        if default_date:
            defaults['year'] = fields.Date.from_string(default_date).year
            defaults['month'] = fields.Date.from_string(default_date).month
        return defaults

    @api.depends('year')
    def _compute_is_leap_year(self):
        for rec in self:
            rec.is_leap_year = bool(rec.year and calendar.isleap(int(rec.year)))

    def _get_blocked_day_numbers(self, year=None, month=None):
        year = year or self.year
        month = month or self.month
        if not year or not month:
            return set()

        blocked = set()
        params = self.env['ir.config_parameter'].sudo()
        weekday_off_map = {
            0: params.get_param('attendance_register.is_monday_off', default=False),
            1: params.get_param('attendance_register.is_tuesday_off', default=False),
            2: params.get_param('attendance_register.is_wednesday_off', default=False),
            3: params.get_param('attendance_register.is_thursday_off', default=False),
            4: params.get_param('attendance_register.is_friday_off', default=False),
            5: params.get_param('attendance_register.is_saturday_off', default=False),
            6: params.get_param('attendance_register.is_sunday_off', default=False),
        }

        last_day = calendar.monthrange(int(year), int(month))[1]
        for day_number in range(1, last_day + 1):
            weekday = date(int(year), int(month), day_number).weekday()
            if weekday_off_map.get(weekday):
                blocked.add(day_number)

        holiday_month = self.holiday_month_id or self.env['attendance.month.holiday'].search([
            ('policy_id', '!=', False),
            ('year', '=', int(year)),
            ('month', '=', int(month)),
        ], limit=1)
        if holiday_month and hasattr(holiday_month, 'get_blocked_days'):
            blocked.update(holiday_month.get_blocked_days())

        return blocked

    def _reset_invalid_day_fields(self, vals):
        year = vals.get('year', self.year)
        month = vals.get('month', self.month)
        if not year or not month:
            return vals

        blocked_days = self._get_blocked_day_numbers(year, month)
        for day_number in range(1, 32):
            field_name = f'day_{day_number}'
            if day_number > calendar.monthrange(int(year), int(month))[1]:
                if field_name in vals and vals[field_name] not in (False, None):
                    vals[field_name] = False
            elif day_number in blocked_days and field_name in vals and vals[field_name] not in (False, None):
                vals[field_name] = False
        return vals

    @api.onchange('year', 'month')
    def _onchange_year_month(self):
        if not self.year or not self.month:
            return

        days_in_month = calendar.monthrange(int(self.year), int(self.month))[1]
        blocked_days = self._get_blocked_day_numbers(self.year, self.month)
        for day_number in range(1, 32):
            field_name = f'day_{day_number}'
            if day_number > days_in_month or day_number in blocked_days:
                setattr(self, field_name, False)

    @api.constrains('student_id', 'year', 'month')
    def _check_duplicate_student_month(self):
        for rec in self:
            if not rec.student_id or rec.year is None or rec.month is None:
                continue

            existing = self.env['attendance.register'].search([
                ('student_id', '=', rec.student_id.id),
                ('year', '=', rec.year),
                ('month', '=', rec.month),
                ('id', '!=', rec.id),
            ], limit=1)

            if existing:
                raise ValidationError(_(
                    "The student is already registered for this month (%s/%s)."
                    % (rec.month, rec.year)
                ))

    def _validate_year_month(self, year, month):
        if year is None or month is None:
            return
        today = fields.Date.context_today(self)
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            raise ValidationError(_('Month must be between 1 and 12.'))
        if year > today.year or year < 1900:
            raise ValidationError(_('Year cannot be greater than the current year or less than 1900.'))
        if year == today.year and month > today.month:
            raise ValidationError(_('Month cannot be greater than the current month.'))

