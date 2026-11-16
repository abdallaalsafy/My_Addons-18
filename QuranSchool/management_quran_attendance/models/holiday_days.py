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

    # =============================== Builtin Functions ==============================
    def _check_policy_not_locked(self, policies):
        if self.env.user.has_group('management_quran_office_core.group_quran_office_manager'):
            return
        for policy in policies.filtered('is_locked'):
            raise ValidationError(_('This policy day is locked. Only managers can edit record of policy: %s.', policy.name))

    @api.model_create_multi
    def create(self, vals_list):
        policies = self.env['attendance.holiday.policy'].browse(
            [v['policy_id'] for v in vals_list if v.get('policy_id')])
        self._check_policy_not_locked(policies)
        return super().create(vals_list)

    def write(self, vals):
        self._check_policy_not_locked(self.policy_id)
        if vals.get('policy_id'):
            self._check_policy_not_locked(self.env['attendance.holiday.policy'].browse(vals['policy_id']))
        return super().write(vals)

    def unlink(self):
        self._check_policy_not_locked(self.policy_id)
        return super().unlink()
    
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
