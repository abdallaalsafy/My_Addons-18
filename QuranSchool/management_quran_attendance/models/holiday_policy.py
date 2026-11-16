import calendar
from datetime import date
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttendanceHolidayPolicy(models.Model):
    _name = 'attendance.holiday.policy'
    _inherit = ['school.organization.mixin']
    _description = 'Attendance Holiday Policy'
    _order = 'start_date desc, name'

    name = fields.Char(string='Policy Name', required=True,)
    start_date = fields.Date(string='Start Date',help="The day is not included in the holiday policy.")
    end_date = fields.Date(string='End Date',help="The day is not included in the holiday policy.")

    is_saturday_off = fields.Boolean(string='Saturday')
    is_sunday_off = fields.Boolean(string='Sunday')
    is_monday_off = fields.Boolean(string='Monday')
    is_tuesday_off = fields.Boolean(string='Tuesday')
    is_wednesday_off = fields.Boolean(string='Wednesday')
    is_thursday_off = fields.Boolean(string='Thursday')
    is_friday_off = fields.Boolean(string='Friday')

    is_locked = fields.Boolean(string='Locked', default=False, copy=False)
    active = fields.Boolean(string='Active', default=True)

    holiday_day_ids = fields.One2many('attendance.holiday.day', 'policy_id', string='Exceptional Holidays')

    _sql_constraints = [
        ('unique_policy_name', 'unique(name)', 'Policy name must be unique.')
    ]

    # =============================== Builtin Functions ==============================
    def write(self, vals):
        if not self.env.user.has_group('management_quran_office_core.group_quran_office_manager'):
            for record in self.filtered('is_locked'):
                raise ValidationError(_('This policy is locked. Only managers can edit record: %s.', record.name))
        return super().write(vals)

    def unlink(self):
        if not self.env.user.has_group('management_quran_office_core.group_quran_office_manager'):
            for record in self.filtered('is_locked'):
                raise ValidationError(_('This policy is locked. Only managers can delete record: %s.', record.name))
        return super().unlink()

# ========================= Constraints =========================
    @api.constrains("start_date","end_date")
    def _check_start_end_date(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_('The end date or start date is not valid.'))

    # =============================== Action Functions ==============================
    def action_lock(self):
        self.write({'is_locked': True,})
        return True

    def action_unlock(self):
        if not self.env.user.has_group('management_quran_office_core.group_quran_office_manager'):
            raise ValidationError(_('Only managers can unlock this policy.'))
        self.write({'is_locked': False,})
        return True

# ======================== Help Function =======================================
    def _validate_is_policy_valid(self,year, month):
        if not self.env['attendance.register']._validate_year_month(year,month):
            return False
        
        reg_date = date(year, month, 1)
        start_date_policy = self.start_date or date.min
        end_date_policy = self.end_date or date.max
        start_year, start_month = start_date_policy.year, start_date_policy.month
        end_year, end_month = end_date_policy.year, end_date_policy.month
        is_policy_valid = (
            (not start_date_policy or date(start_year, start_month, 1) <= reg_date)
            and
            (not end_date_policy or reg_date <= date(end_year, end_month, 1))
        )

        return is_policy_valid
    
    def _get_days_of_holiday_numbers(self, year, month):
        if not self._validate_is_policy_valid(year, month):
            return set()

        holidays = set()
        weekday_off_map = {
            0: self.is_monday_off,
            1: self.is_tuesday_off,
            2: self.is_wednesday_off,
            3: self.is_thursday_off,
            4: self.is_friday_off,
            5: self.is_saturday_off,
            6: self.is_sunday_off,
        }

        last_day = calendar.monthrange(year, month)[1]
        for day_number in range(1, last_day + 1):
            weekday = date(year, month, day_number).weekday()
            if weekday_off_map.get(weekday):
                holidays.add(day_number)

        for holiday_day in self.holiday_day_ids:
            if holiday_day.holiday_date and holiday_day.holiday_date.year == year and holiday_day.holiday_date.month == month:
                holidays.add(holiday_day.holiday_date.day)

        return holidays
    