from odoo import fields, models


class AttendanceRegisterSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_management_quran_subscription = fields.Boolean(
        'Subscription Module',
        help="Install Subscription Module",
    )
    module_management_quran_memorization = fields.Boolean(
            'Memorization Module',
            help="Install Memorization Module",
        )
    module_management_quran_competition = fields.Boolean(
            'Competition Module',
            help="Install Competition Module",
        )
    module_management_quran_attendance = fields.Boolean(
            'Attendance Module',
            help="Install Attendance Module",
        )
