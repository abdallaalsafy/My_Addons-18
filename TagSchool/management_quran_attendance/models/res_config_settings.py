from odoo import api, fields, models


class AttendanceRegisterSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_day_value = fields.Boolean(string='Default day value')
    is_sunday_off = fields.Boolean(string='Sunday')
    is_monday_off = fields.Boolean(string='Monday')
    is_tuesday_off = fields.Boolean(string='Tuesday')
    is_wednesday_off = fields.Boolean(string='Wednesday')
    is_thursday_off = fields.Boolean(string='Thursday')
    is_friday_off = fields.Boolean(string='Friday')
    is_saturday_off = fields.Boolean(string='Saturday')

    @api.model
    def get_values(self):
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo()
        res.update(
            auto_day_value=param.get_param('attendance_register.auto_day_value', default=True),
            is_sunday_off=param.get_param('attendance_register.is_sunday_off', default=False),
            is_monday_off=param.get_param('attendance_register.is_monday_off', default=False),
            is_tuesday_off=param.get_param('attendance_register.is_tuesday_off', default=False),
            is_wednesday_off=param.get_param('attendance_register.is_wednesday_off', default=False),
            is_thursday_off=param.get_param('attendance_register.is_thursday_off', default=False),
            is_friday_off=param.get_param('attendance_register.is_friday_off', default=False),
            is_saturday_off=param.get_param('attendance_register.is_saturday_off', default=False),
        )
        return res

    def set_values(self):
        super().set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param('attendance_register.auto_day_value', self.auto_day_value)
        param.set_param('attendance_register.is_sunday_off', self.is_sunday_off)
        param.set_param('attendance_register.is_monday_off', self.is_monday_off)
        param.set_param('attendance_register.is_tuesday_off', self.is_tuesday_off)
        param.set_param('attendance_register.is_wednesday_off', self.is_wednesday_off)
        param.set_param('attendance_register.is_thursday_off', self.is_thursday_off)
        param.set_param('attendance_register.is_friday_off', self.is_friday_off)
        param.set_param('attendance_register.is_saturday_off', self.is_saturday_off)
