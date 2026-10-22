import calendar
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AttendanceRegister(models.Model):
    _name = 'attendance.register'
    _description = 'Attendance Register'

    _ATTENDANCE_STATUS = [
        ('present', '✅ Present'),
        ('absent', '❌ Absent'),
        ('holiday', '🏖️ Holiday'),
        ('excused', '📝 Excused'),
        ('sick', '🤒 Sick'),
        ('late', '⏰ Late'),
        ('unrestricted', '🔓 Unrestricted'),
    ]


    # ========================== Logic Functions =============================
    def _default_holiday_policy_record(self):
        param = self.env['ir.config_parameter'].sudo()
        stored_policy_id = param.get_param('attendance_register.default_holiday_policy_id')
        if stored_policy_id:
            policy = self.env['attendance.holiday.policy'].browse(int(stored_policy_id))
            if policy.exists():
                return policy
        else:
            policy = self.env.ref('management_quran_attendance.attendance_default_holiday_policy', raise_if_not_found=False)
            if policy:
                return policy
        return False
    
    student_id = fields.Many2one('res.partner', string='Students', domain="[('is_student', '=', True)]", required=True)
    date = fields.Date(string='Date', compute="_compute_date_from_year_and_month", store=True)
    year = fields.Integer(string='Year')
    month = fields.Integer(string='Month')
    day = fields.Integer(string='Day', compute="_compute_day_from_year_and_month", store=False)

    holiday_policy_id = fields.Many2one('attendance.holiday.policy', string='Holiday Policy', default=_default_holiday_policy_record,)
    is_policy_valid = fields.Boolean(string='Is Policy Valid', compute="_compute_is_policy_valid",store=True)
    
    office_id = fields.Many2one('quran.office.office', string='Office', required=True)
    class_id = fields.Many2one('quran_office.class', string='Class', domain="[('office_id', '=?', office_id)]")
    teacher_id = fields.Many2one('res.partner', string='Teacher', domain="[('is_teacher', '=', True)]")
    
    is_leap_year = fields.Boolean(string='Is Leap Year', compute='_compute_is_leap_year', store=False)
    day_1 = fields.Selection(string='01', selection=_ATTENDANCE_STATUS)
    day_2 = fields.Selection(string='02', selection=_ATTENDANCE_STATUS)
    day_3 = fields.Selection(string='03', selection=_ATTENDANCE_STATUS)
    day_4 = fields.Selection(string='04', selection=_ATTENDANCE_STATUS)
    day_5 = fields.Selection(string='05', selection=_ATTENDANCE_STATUS)
    day_6 = fields.Selection(string='06', selection=_ATTENDANCE_STATUS)
    day_7 = fields.Selection(string='07', selection=_ATTENDANCE_STATUS)
    day_8 = fields.Selection(string='08', selection=_ATTENDANCE_STATUS)
    day_9 = fields.Selection(string='09', selection=_ATTENDANCE_STATUS)
    day_10 = fields.Selection(string='10', selection=_ATTENDANCE_STATUS)
    day_11 = fields.Selection(string='11', selection=_ATTENDANCE_STATUS)
    day_12 = fields.Selection(string='12', selection=_ATTENDANCE_STATUS)
    day_13 = fields.Selection(string='13', selection=_ATTENDANCE_STATUS)
    day_14 = fields.Selection(string='14', selection=_ATTENDANCE_STATUS)
    day_15 = fields.Selection(string='15', selection=_ATTENDANCE_STATUS)
    day_16 = fields.Selection(string='16', selection=_ATTENDANCE_STATUS)
    day_17 = fields.Selection(string='17', selection=_ATTENDANCE_STATUS)
    day_18 = fields.Selection(string='18', selection=_ATTENDANCE_STATUS)
    day_19 = fields.Selection(string='19', selection=_ATTENDANCE_STATUS)
    day_20 = fields.Selection(string='20', selection=_ATTENDANCE_STATUS)
    day_21 = fields.Selection(string='21', selection=_ATTENDANCE_STATUS)
    day_22 = fields.Selection(string='22', selection=_ATTENDANCE_STATUS)
    day_23 = fields.Selection(string='23', selection=_ATTENDANCE_STATUS)
    day_24 = fields.Selection(string='24', selection=_ATTENDANCE_STATUS)
    day_25 = fields.Selection(string='25', selection=_ATTENDANCE_STATUS)
    day_26 = fields.Selection(string='26', selection=_ATTENDANCE_STATUS)
    day_27 = fields.Selection(string='27', selection=_ATTENDANCE_STATUS)
    day_28 = fields.Selection(string='28', selection=_ATTENDANCE_STATUS)
    day_29 = fields.Selection(string='29', selection=_ATTENDANCE_STATUS)
    day_30 = fields.Selection(string='30', selection=_ATTENDANCE_STATUS)
    day_31 = fields.Selection(string='31', selection=_ATTENDANCE_STATUS)

    present_days = fields.Integer(string='Present Days', compute='_compute_status_summary', store=True)
    absent_days = fields.Integer(string='Absent Days', compute='_compute_status_summary', store=True)
    holiday_days = fields.Integer(string='Holiday Days', compute='_compute_status_summary', store=True)
    excused_days = fields.Integer(string='Excused Days', compute='_compute_status_summary', store=True)
    sick_days = fields.Integer(string='Sick Days', compute='_compute_status_summary', store=True)
    late_days = fields.Integer(string='Late Days', compute='_compute_status_summary', store=True)
    study_days = fields.Integer(string='Study Days', compute='_compute_status_summary', store=True)


# ========================= CRUD Overrides =========================
    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        date_value = self.date or self.env.context.get('default_date') or fields.Date.today()
        year, month,_ = self._get_year_month_from_date(date_value)
        defaults['year'] = year
        defaults['month'] = month
        return defaults
    
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
     
        # Because (onchange Function (_onchange_holiday_policy_id)) doesn't work with multy-create in list view from wizard.
        # So, we need to apply holiday day constraints for all records in the list.
        if self.env.context.get('create_lines_from_outside') == True:
            for rec in res:
                rec._apply_holiday_day_constraints(
                            rec.year,
                            rec.month,
                            rec.holiday_policy_id,
                            rec.is_policy_valid)
        return res

    def write(self, vals):
        res = super().write(vals)

        # Because (onchange Function (_onchange_holiday_policy_id)) doesn't work with multy-write in list view.
        # So, we need to apply holiday day constraints for all records in the list.
        # But if user checked one recored in list view and update it, we can't apply holiday day constraints this checked record.
        if len(self) > 1 and ('year' in vals or 'month' in vals or 'holiday_policy_id' in vals): 
            for rec in self:
                rec._apply_holiday_day_constraints(
                            rec.year,
                            rec.month,
                            rec.holiday_policy_id,
                            rec.is_policy_valid)
        return res
    
#========================= Compute Functions =========================
    @api.depends('year', 'month')
    def _compute_day_from_year_and_month(self):
        today = fields.Date.context_today(self)
        for rcrd in self:
            if rcrd.year and rcrd.month and today.year == rcrd.year and today.month == rcrd.month:
                rcrd.day = today.day
            else:
                rcrd.day = 0

    @api.depends('year')
    def _compute_is_leap_year(self):
        for rec in self:
            rec.is_leap_year = bool(rec.year and calendar.isleap(int(rec.year)))

    @api.depends('year','month')
    def _compute_date_from_year_and_month(self):
        for rcrd in self:
            if rcrd.year > 0 and (12 >= rcrd.month > 0):
                rcrd.date = fields.Date.to_string(date(int(rcrd.year), int(rcrd.month), 1))

    @api.depends('year', 'month', 'holiday_policy_id', 'holiday_policy_id.start_date', 'holiday_policy_id.end_date')
    def _compute_is_policy_valid(self):
        for reg in self:
            reg.is_policy_valid = reg.holiday_policy_id._validate_is_policy_valid(reg.year, reg.month)

    @api.depends('year', 'month', 'day_1', 'day_2', 'day_3', 'day_4', 'day_5', 'day_6', 'day_7', 'day_8', 'day_9', 'day_10',
                 'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                 'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31')
    def _compute_status_summary(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.year or not rec.month or not rec._validate_year_month(rec.year, rec.month):
                for field_name in ['present_days', 'absent_days', 'holiday_days', 'excused_days', 'sick_days', 'late_days', 'study_days']:
                    setattr(rec, field_name, 0)
                continue

            last_day = calendar.monthrange(rec.year, rec.month)[1]
            limit_day = last_day
            if rec.year == today.year and rec.month == today.month:
                limit_day = today.day

            status_totals = {
                'present': 0,
                'absent': 0,
                'holiday': 0,
                'excused': 0,
                'sick': 0,
                'late': 0,
            }

            for day_number in range(1, limit_day + 1):
                field_name = f'day_{day_number}'
                status = getattr(rec, field_name, False)
                if status in status_totals:
                    status_totals[status] += 1

            rec.present_days = status_totals['present'] + status_totals['late']
            rec.absent_days = status_totals['absent'] + status_totals['excused'] + status_totals['sick']
            rec.holiday_days = status_totals['holiday']
            rec.excused_days = status_totals['excused']
            rec.sick_days = status_totals['sick']
            rec.late_days = status_totals['late']
            rec.study_days = status_totals['present'] + status_totals['absent'] + status_totals['late'] + status_totals['excused'] + status_totals['sick']
    
# ========================= OnChange Functions =========================
    @api.onchange('holiday_policy_id', 'year', 'month')
    def _onchange_holiday_policy_id(self):
        self._apply_holiday_day_constraints(
            self.year,
            self.month,
            self.holiday_policy_id,
            self.is_policy_valid)

    @api.onchange('student_id')
    def _onchange_student_id(self):
        """When student changes, populate office, class, and teacher fields"""
        if self.student_id:
            self.office_id = self.student_id.office_id
            self.class_id = self.student_id.class_id
            self.teacher_id = self.student_id.teacher_id

    @api.onchange('office_id')
    def _onchange_office_id(self):
        """Clear class_id when office changes to ensure proper filtering."""
        if self.class_id and self.class_id.office_id != self.office_id:
            self.class_id = False

    @api.onchange('class_id')
    def _onchange_class_id(self):
        """Auto-fill teacher_id when class is selected."""
        if self.class_id:
            self.office_id = self.class_id.office_id
        if self.class_id and self.class_id.teacher_id:
            self.teacher_id = self.class_id.teacher_id

    @api.onchange('teacher_id')
    def _onchange_teacher_id(self):
        if self.teacher_id and not self.class_id:
            self.class_id = self.teacher_id.class_ids[0]

# ========================= constraints Functions =========================
    @api.constrains('year', 'month')
    def _check_month_year(self):
        for rec in self:
            if not rec._validate_year_month(rec.year,rec.month):
                raise ValidationError(_('Month or Year is invalid.'))

    @api.constrains('student_id', 'year', 'month','office_id', 'class_id', 'teacher_id')
    def _check_duplicate_student_month(self):
        for rec in self:
            if not rec.student_id or rec.year is None or rec.month is None:
                continue

            existing = self.env['attendance.register'].search([
                ('student_id', '=', rec.student_id.id),
                ('year', '=', rec.year),
                ('month', '=', rec.month),
                ('office_id', '=', rec.office_id.id),
                ('id', '!=', rec.id),
            ], limit=1)

            if existing:
                raise ValidationError(_(
                    "The student is already registered for this month and scope (%s/%s)."
                    % (rec.month, rec.year)
                ))

    @api.constrains('day_1', 'day_2', 'day_3', 'day_4', 'day_5', 'day_6', 'day_7', 'day_8', 'day_9', 'day_10',
                   'day_11', 'day_12', 'day_13', 'day_14', 'day_15', 'day_16', 'day_17', 'day_18', 'day_19', 'day_20',
                   'day_21', 'day_22', 'day_23', 'day_24', 'day_25', 'day_26', 'day_27', 'day_28', 'day_29', 'day_30', 'day_31',
                   'year', 'month')
    def _check_day_sequence(self):
        for rec in self:
            if not self._validate_year_month(rec.year, rec.month):
                continue

            last_day = calendar.monthrange(rec.year, rec.month)[1]
            previous_blank = False

            for day_number in range(1, last_day + 1):
                field_name = f'day_{day_number}'
                value = getattr(rec, field_name, False)

                if not value:
                    previous_blank = True
                    continue

                if previous_blank and value != 'holiday':
                    raise ValidationError(_(
                        "You cannot save day %s before a previous day is filled."
                        % day_number
                    ))

                previous_blank = False
            
# ========================= Helper Functions =========================

    def _apply_holiday_day_constraints(self, year, month, policy):
        if not self._validate_year_month(year, month):
            return

        blocked_days = set()
        if policy:
            blocked_days = policy._get_days_of_holiday_numbers(year, month)

        last_day = calendar.monthrange(year, month)[1]
        for day_number in range(1, 32):
            field_name = f'day_{day_number}'
            current_value = getattr(self, field_name, False)
            if day_number > last_day:
                setattr(self, field_name, False)
            elif policy and day_number in blocked_days:
                setattr(self, field_name, 'holiday')
            elif policy and current_value == 'holiday':
                setattr(self, field_name, False)
            elif self.day > 0 and day_number > self.day:
                setattr(self, field_name, False)
    
    def _get_year_month_from_date(self,date_value):
        if not date_value:
            return None, None
        dt = fields.Date.from_string(date_value)
        return dt.year, dt.month, dt.day
    
    def _validate_year_month(self, year, month):
        today = fields.Date.context_today(self)
        if (month < 1 or month > 12) or (year > today.year or year < 1900) or (year == today.year and month > today.month):
            return False
        return True
