# -*- coding: utf-8 -*-

from odoo.addons.management_quran_office_core.models.utils import get_detailed_age
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from .constants import _STATUS_SELECTION, _STATE_SELECTION

class QuranCompetitionParticipant(models.Model):
    _name = 'quran.competition.participant'
    _inherit = ['memorization.mixin', 'school.organization.mixin']
    _description = 'Quran Competition Participant'

    
    name = fields.Char(
        'Registration Number',
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    competition_id = fields.Many2one(
        'quran.competition',
        string='Competition',
        required=True,
        ondelete='restrict',
        help="Competition this participant belongs to"
    )
    requirement_id = fields.Many2one(
        related='competition_id.requirement_id',
        string='Requirements',
    )
    student_id = fields.Many2one(
        'res.partner',
        string='Student',
        required=True,
        domain="[('is_student', '=', True)]",
        ondelete='restrict',
        copy=False,
        help="Student participating in the competition"
    )
    age_from_id = fields.Char('Detailed Age', compute="_compute_age_to_competition_date")
    age_years = fields.Integer('Age (Years)', compute="_compute_age_to_competition_date")
    age_months = fields.Integer('Age (Months)', compute="_compute_age_to_competition_date")
    age_days = fields.Integer('Age (Days)', compute="_compute_age_to_competition_date")

    registration_number = fields.Char(
        'Source Registration',
        copy=False,
        help="Unique registration number for the participant"
    )
    registration_date = fields.Datetime(
        'Registration Date',
        required=True,
        default=fields.Datetime.now,
        help="Date and time of registration"
    )
    # Prize Fields ===============================================
    monetary_prize = fields.Monetary(
        'Monetary Prize',
        currency_field='currency_id',
        help="Amount of monetary prize awarded to participant"
    )
    in_kind_prize = fields.Text(
        'In-Kind Prize',
        help="Description of in-kind prize awarded to participant"
    )
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Currency for subscription fee"
    )
# ================= Basic Fields Of Competition Participant =========================
    competition_test_grade = fields.Integer(
        related='competition_id.test_grade',
        string='Competition Test Grade',
        help="Test grade defined in the competition"
    )
    score = fields.Float(
        'Score',
        digits=(5, 2),
        help="Score obtained by the participant"
    )
    evaluation_percentage = fields.Float(
        string='Percentage %',
        digits=(5, 2),
        compute='_compute_evaluation_percentage',
        store=True,
        help='Final percentage of score against the competition grade'
    )
    result_id = fields.Many2one(
        'quran.competition.participant.result',
        string='Evaluation Result',
        help='Result rule applied to this participant after evaluation'
    )
    level_id = fields.Many2one(
        'quran.competition.level',
        string='Competition Level',
        domain="[('competition_id', '=', competition_id)]",
        help="Level of memorization for this participant in the competition"
    )
    state = fields.Selection(_STATE_SELECTION, 'State',
        default='draft',
        required=True,
        help="Current status of the participant"
    )
    status = fields.Selection(_STATUS_SELECTION, 'Status',
        help="Evaluation status based on performance"
    )
    reason_disqualified = fields.Html('reason disqualified')
    #========================================
    notes = fields.Text(
        'Evaluation Notes',
        help="Notes about participant performance"
    )


    _sql_constraints = [('competition_student_uniq', 'unique(competition_id,student_id)', 'Participant must be unique per competition!'),]
    
# ========================= Built-in Methods =========================
    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """Override _search to ensure proper ordering of participants"""
        orders = self.env.context.get('main_search_order')
        if orders:
            order = orders
        rtn = super()._search(domain, offset, limit, order)
        return rtn

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate registration number"""
        competitions = self.env['quran.competition'].browse(
            [v['competition_id'] for v in vals_list if v.get('competition_id')])
        if competitions.filtered(lambda c: c.status == 'closed'):
            raise ValidationError(_('Cannot add participants to a closed competition'))
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quran.competition.participant')
        return super().create(vals_list)

    def write(self, vals):
        if self.filtered(lambda p: p.competition_id.status == 'closed'):
            raise ValidationError(_('Cannot modify participant in a closed competition'))
        if 'state' in vals and vals['state'] != 'disqualified':
            vals['reason_disqualified'] = ''
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda p: p.competition_id.status == 'closed'):
            raise ValidationError(_('Cannot delete participant in a closed competition'))
        return super().unlink()

    @api.depends('name', 'student_id')
    def _compute_display_name(self):
        """Override _compute_display_name to show registration number and participant name"""
        for participant in self:
            participant.display_name = f"[{participant.name or ''}] {participant.student_id.name or 'Unknown'}"
    
# ========================= OnChange Methods =========================
    @api.onchange('student_id')
    def _onchange_student_id(self):
        """Auto-fill office, class, teacher, and memorization method from student"""
        if self.student_id:
            # Auto-fill office, class, teacher
            self.office_id = self.student_id.office_id
            self.class_id = self.student_id.class_id
            self.teacher_id = self.student_id.teacher_id
            self.memorization_method = self.student_id.memorization_method
            # Check if student has memorized full Quran (30 juz)
            if self.student_id.is_quran_memorizer:
                self.juze_amount = 30.0

    @api.onchange('juze_amount', 'competition_id')
    def _onchange_juze_amount(self):
        """Auto-fill level_id based on juze_amount and competition levels"""
        if self.juze_amount and self.competition_id and not self.level_id:
            self.level_id = self.get_levels_for_participant()

    @api.onchange('evaluation_percentage', 'competition_id')
    def _onchange_evaluation_percentage(self):
        """Auto-fill status and result_id based on evaluation percentage"""
        if self.competition_id:
             self.result_id,self.status = self.get_status_from_percentage()

# ============================ Computed Functions ===================================
    @api.depends('competition_id.competition_date', 'student_id.birth_date', 'student_id.id_number')
    def _compute_age_to_competition_date(self):
        """Compute age of student to competition date using unified functions."""
        for participant in self:
            if participant.student_id and participant.competition_id:
                participant.age_from_id,participant.age_years,participant.age_months,participant.age_days = get_detailed_age(national_id=participant.student_id.id_number, birth_date=participant.student_id.birth_date,today=participant.competition_id.competition_date)
            else:
                participant.age_from_id = ''
                participant.age_years = 0
                participant.age_months = 0
                participant.age_days = 0

    @api.depends('score', 'competition_id.test_grade')
    def _compute_evaluation_percentage(self):
        for participant in self:
            if participant.competition_id.test_grade > 0:
                participant.evaluation_percentage = (participant.score / participant.competition_id.test_grade) * 100.0
            else:
                participant.evaluation_percentage = 0.0

# ========================= Constrains Methods =========================
    @api.constrains('score')
    def _check_score_limits(self):
        """Validate score does not exceed competition test grade and is not negative"""
        for participant in self:
            # Check if score is negative
            if participant.score < 0:
                raise ValidationError(_('Score cannot be negative'))

            # Check if score exceeds competition test grade
            if participant.score > participant.competition_test_grade:
                raise ValidationError(_('Score (%.2f) cannot exceed competition test grade (%d)') % (
                    participant.score, participant.competition_test_grade))

    @api.constrains('juze_amount', 'memorization_method','surah_id', 'surah_ids', 'ayah_num')
    def _constrains_memorization_amount_consistency(self):
        """Validate memorization amount consistency with surah and ayah calculation."""
        for record in self:
            if record.memorization_method != 'mixed':
                record._check_memorization_amount_consistency()
            else:
                record._constrain_memorization_amount()
    
    @api.constrains('registration_date', 'competition_id')
    def _check_registration_date_limits(self):
        """Validate registration_date is not in future and not before competition_date"""
        for participant in self:
            if participant.registration_date and participant.competition_id:
                # Check if registration date is in future
                if participant.registration_date > fields.Datetime.now():
                    raise ValidationError(_('Registration date cannot be in the future'))
                
                # Check if registration date is before competition date
                if participant.competition_id.competition_date:
                    if participant.registration_date.date() > participant.competition_id.competition_date:
                        raise ValidationError(_('Registration date cannot be after competition date (%s)') % 
                                           participant.competition_id.competition_date.strftime('%Y-%m-%d'))

# ========================= Action Methods =========================
    def action_check_participant_eligibility(self):
        """Check participant eligibility"""
        for participant in self:
            if not participant.requirement_id:
                raise ValidationError(_('No requirement defined for this competition %s') % participant.competition_id.name)
            no_messages,messages = participant.check_participant_eligibility()
            participant.state = 'disqualified' if not no_messages else 'confirmed'
            participant.reason_disqualified = ' - '.join(messages)
            if not no_messages and len(self) == 1:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'warning',
                        'title': _('Validation of requirements'),
                        'message': ' - '.join(messages) ,
                        'next': {'type': 'ir.actions.act_window_close'},
                    },
                }

    def action_match_level_to_juze_amount(self):
        """Match level_id based on juze_amount and competition levels"""
        for participant in self:
            participant.level_id = participant.get_levels_for_participant()

    def action_evaluate_participant(self):
        """Evaluate participant based on score and competition rules"""
        for participant in self:
            if participant.score <= 0:
                raise ValidationError(_('Score must be set before evaluation'))
            participant.result_id,participant.status = participant.get_status_from_percentage()

# ============================= Helper Function ===================================
    def check_participant_eligibility(self):
        """Check if participant meets all requirements,Returns: (eligible, messages)"""
        self.ensure_one()
        messages = []

        requirement_id = self.competition_id.requirement_id
        if not requirement_id:
            return 0,[]
        
        # Check participant numbers
        if requirement_id.participant_nums > 0 and (self.competition_id.participants_count > requirement_id.participant_nums or self.competition_id.status == 'completed'):
            messages.append(_("Participant limit reached for this requirement"))

        # Check age requirements
        age = self.age_years
        min_age = requirement_id.min_age
        max_age = requirement_id.max_age
        if max_age > 0 and (age < min_age or age > max_age):
            messages.append(_("Age (%d) is not within the required range (%d - %d)") % (age, min_age, max_age))

        # Check memorization requirements
        if requirement_id.memorization_required:
            if requirement_id.specific_surahs_required:
                participant_surah_ids = self.surah_ids.ids
                required_surah_ids = requirement_id.required_surah_ids.ids
                if not set(required_surah_ids).issubset(set(participant_surah_ids)):
                    messages.append(_("Participant has not memorized all required surahs"))
            else:
                participant_juze_amount = self.juze_amount
                min_memorization_amount = requirement_id.min_memorization_amount
                max_memorization_amount = requirement_id.max_memorization_amount
                if not (min_memorization_amount <= participant_juze_amount <= max_memorization_amount):
                    messages.append(_("Memorization amount (%.2f Juz) is not within the required range (%.2f - %.2f Juz)") % (
                        participant_juze_amount, min_memorization_amount, max_memorization_amount))
            
        # Check previous competition requirements
        message = self.check_eligibility(requirement_id)
        if not message['eligible']:
            messages.append(message['reason'])
        
        # Check office/class/teacher requirements
        if requirement_id.office_ids and self.office_id not in requirement_id.office_ids:
            messages.append(_("Participant's office is not in the required offices"))
        if requirement_id.teacher_ids and self.teacher_id not in requirement_id.teacher_ids:
            messages.append(_("Participant's teacher is not in the required teachers"))

        return len(messages) == 0, messages

    def check_eligibility(self, requirement_id):
        """Return whether a participant satisfies these requirements."""
        self.ensure_one()

        required_tag_ids = requirement_id.required_tag_ids
        required_competition_ids = requirement_id.required_competition_ids

        # Previous registration records of the participant.
        history = self.student_id.participant_ids.filtered(lambda rec: rec.state == "confirmed" and rec.id != self.id)

        # Optional scope: explicit competitions OR matching tags.
        has_scope = bool(required_competition_ids or required_tag_ids)

        def matches_scope(participant):
            competition = participant.competition_id
            matches_competition = (competition in required_competition_ids)
            matches_tag = bool(competition.tag_ids & required_tag_ids)
            return matches_competition or matches_tag

        if has_scope:
            matching_history = history.filtered(matches_scope)
            other_history = history - matching_history
        else:
            matching_history = history
            other_history = history

        # 1. Validate previous registration requirements.
        status = requirement_id.registration_status

        if status == "registered" and not matching_history:
            return {
                "eligible": False,
                "reason": _(
                    "The participant has no previous registration "
                    "matching the required competitions or tags."
                ),
            }

        if status == "not_registered" and matching_history:
            return {
                "eligible": False,
                "reason": _(
                    "The participant has already registered in "
                    "a restricted competition."
                ),
            }

        # 2. Determine which previous levels must be exceeded.
        if requirement_id.highest_level_yet:
            if status == "registered":
                comparison_history = matching_history
            elif status == "not_registered" and has_scope:
                comparison_history = other_history
            else:
                comparison_history = history

            for participant in comparison_history:
                previous_level = participant.juze_amount
                current_level = self.juze_amount

                if current_level <= previous_level and participant.status in ["superior", "successful"]:
                    return {
                        "eligible": False,
                        "reason": _(
                            "The current memorization level must be "
                            "higher than every applicable previous level."
                        ),
                    }

        return {
            "eligible": True,
            "reason": _("All requirements are satisfied."),
        }

    def get_levels_for_participant(self):
        """Return levels that the participant is eligible for based on their memorization amount."""
        self.ensure_one()
        if not self.competition_id or not self.juze_amount:
            return False
        eligible_levels = self.competition_id.level_ids.filtered(lambda l: l.required_juz <= self.juze_amount).sorted(key=lambda l: l.required_juz, reverse=True)[:1]
        return eligible_levels

    def get_status_from_percentage(self):
        """Return status based on evaluation percentage"""
        self.ensure_one()
        if not self.competition_id:
            return False,False
        eligible_status = self.competition_id.evaluation_rule_ids.filtered(lambda l: l.percentage <= self.evaluation_percentage).sorted(key=lambda l: l.percentage, reverse=True)[:1]
        return eligible_status,eligible_status.result_status if eligible_status else False