from odoo import api, fields, models


class AttendanceRegisterSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _default_default_holiday_policy(self):
        default_policy = self.env.ref('management_quran_attendance.attendance_default_holiday_policy', raise_if_not_found=False)
        return default_policy


    holiday_policy_id = fields.Many2one(
        'attendance.holiday.policy',
        string='Default absence policy',
        default=_default_default_holiday_policy,
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo()
        default_policy = self._default_default_holiday_policy()
        stored_policy_id = param.get_param('attendance_register.default_holiday_policy_id')
        if stored_policy_id:
            stored_policy = self.env['attendance.holiday.policy'].browse(int(stored_policy_id))
            if stored_policy.exists():
                default_policy = stored_policy

        res.update(holiday_policy_id=default_policy.id if default_policy else False,)
        return res

    def set_values(self):
        super().set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param(
            'attendance_register.default_holiday_policy_id',
            self.holiday_policy_id.id if self.holiday_policy_id else False,
        )
