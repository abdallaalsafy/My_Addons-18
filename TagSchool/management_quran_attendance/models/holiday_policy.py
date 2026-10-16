from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttendanceHolidayPolicy(models.Model):
    _name = 'attendance.holiday.policy'
    _description = 'Attendance Holiday Policy'
    _order = 'start_date desc, name'

    @api.model
    def _default_day_value(self):
        params = self.env['ir.config_parameter'].sudo()
        return {
            0: params.get_param('attendance_register.is_saturday_off', default=False),
            1: params.get_param('attendance_register.is_sunday_off', default=False),
            2: params.get_param('attendance_register.is_monday_off', default=False),
            3: params.get_param('attendance_register.is_tuesday_off', default=False),
            4: params.get_param('attendance_register.is_wednesday_off', default=False),
            5: params.get_param('attendance_register.is_thursday_off', default=False),
            6: params.get_param('attendance_register.is_friday_off', default=False),
        }

    name = fields.Char(string='Policy Name', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    office_id = fields.Many2one('quran_office.office', string='Office')
    class_id = fields.Many2one('quran_office.class', string='Class', domain="[('office_id', '=', office_id)]")
    teacher_id = fields.Many2one('res.partner', string='Teacher', domain="[('is_teacher', '=', True)]")

    active = fields.Boolean(string='Active', default=True)
    is_saturday_off = fields.Boolean(default=lambda self: self._default_day_value().get(0), string='Saturday')
    is_sunday_off = fields.Boolean(default=lambda self: self._default_day_value().get(1), string='Sunday')
    is_monday_off = fields.Boolean(default=lambda self: self._default_day_value().get(2), string='Monday')
    is_tuesday_off = fields.Boolean(default=lambda self: self._default_day_value().get(3), string='Tuesday')
    is_wednesday_off = fields.Boolean(default=lambda self: self._default_day_value().get(4), string='Wednesday')
    is_thursday_off = fields.Boolean(default=lambda self: self._default_day_value().get(5), string='Thursday')
    is_friday_off = fields.Boolean(default=lambda self: self._default_day_value().get(6), string='Friday')
    holiday_day_ids = fields.One2many('attendance.holiday.day', 'policy_id', string='Exceptional Holidays')

    _sql_constraints = [
        ('unique_policy_name', 'unique(name)', 'Policy name must be unique.')
    ]

    @api.constrains('start_date', 'end_date', 'office_id', 'class_id', 'teacher_id')
    def _check_policy_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(_('End Date must be greater than or equal to Start Date.'))

            domain = [
                ('id', '!=', rec.id),
                ('active', '=', True),
                ('start_date', '<=', rec.end_date),
                ('end_date', '>=', rec.start_date),
                ('office_id', '=', rec.office_id.id if rec.office_id else False),
                ('class_id', '=', rec.class_id.id if rec.class_id else False),
                ('teacher_id', '=', rec.teacher_id.id if rec.teacher_id else False),
            ]

            if self.search(domain, limit=1):
                raise ValidationError(_(
                    'A holiday policy already exists for the same scope and overlapping period.'
                ))
