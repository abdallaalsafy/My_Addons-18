# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QuranCompetitionParticipant(models.Model):
    _name = 'quran.competition.participant'
    _description = 'Quran Competition Participant'
    _order = 'registration_date desc'


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
        ondelete='cascade',
        help="Competition this participant belongs to"
    )
    
    participant_id = fields.Many2one(
        'res.partner',
        string='Participant',
        required=True,
        domain="[('is_student', '=', True)]",
        help="Student participating in the competition"
    )

    age_from_id = fields.Char('Detailed Age',readonly=True)
    age_years = fields.Integer('Age (Years)',)
    age_months = fields.Integer('Age (Months)',)
    age_days = fields.Integer('Age (Days)')

    office_id = fields.Many2one(
        'quran.office.office',
        string='Office',
    )

    class_id = fields.Many2one(
        'quran_office.class',
        string='Class',
        domain="[('office_id', '=?', office_id)]",
    )

    teacher_id = fields.Many2one(
        'res.partner',
        string='Teacher',
        domain="[('is_teacher', '=', True)]"
    )

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

    # ================= Basic Fields Of Competition Participant =========================
    memorization_method = fields.Selection([
        ('from_baqarah', 'Memorization from Al-Baqarah'),
        ('from_nas', 'Memorization from An-Nas'),
        ('mixed', 'Mixed Memorization'),
    ], 'Memorization Method', default='from_nas', required=True,
        help="Method of Quran memorization")
    surah = fields.Many2one(
        'quran_office.surah',
        'Surah',
        readonly=True,
        store=True,
        compute='_compute_surah_aya_from_amount_juz',
        help="Surah where memorization starts"
    )
    ayah = fields.Integer(
        'Ayah',
        readonly=True,
        store=True,
        compute='_compute_surah_aya_from_amount_juz',
        help="Ayah number where memorization starts"
    )
    amount_juz = fields.Float(
        string='Amount (Juz\')',
        digits=(16, 2),
        required=True,
        help="Amount of Quran memorized in Juz' (parts) with decimal precision"
    )
    
    surahes_memorized = fields.Text(
        'Memorized Surahes',
        help="List of surahes memorized by the participant"
    )
    
    score = fields.Float(
        'Score',
        digits=(5, 2),
        help="Score obtained by the participant"
    )
    
    state = fields.Selection([
        ('registered', 'Registered'),
        ('confirmed', 'Confirmed'),
        ('inappropriate', 'Inappropriate'),
        ('withdrawn', 'Withdrawn'),
        ('disqualified', 'Disqualified'),
    ], 'Status',
        default='registered',
        required=True,
        help="Current status of the participant"
    )

    notes = fields.Text(
        'Evaluation Notes',
        help="Notes about participant performance"
    )
    
    # Related Fields from Competition
    competition_test_grade = fields.Integer(
        related='competition_id.test_grade',
        string='Competition Test Grade',
        help="Test grade defined in the competition"
    )
    
    # Prize Fields
    monetary_prize = fields.Float(
        'Monetary Prize',
        digits=(16, 2),
        help="Amount of monetary prize awarded to participant"
    )
    
    in_kind_prize = fields.Text(
        'In-Kind Prize',
        help="Description of in-kind prize awarded to participant"
    )


    # ========================= Built-in Methods =========================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate registration number"""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quran.competition.participant')
        return super().create(vals_list)

    def name_get(self):
        """Override name_get to show registration number and participant name"""
        result = []
        for participant in self:
            if participant.name and participant.participant_id.name:
                name = f"[{participant.name}] {participant.participant_id.name}"
            else:
                name = participant.participant_id.name or 'Unknown'
            result.append((participant.id, name))
        return result

    # ========================= Constrains Methods =========================
    @api.constrains('competition_id', 'participant_id')
    def _check_unique_participant(self):
        """Ensure participant is unique per competition"""
        for participant in self:
            duplicates = self.search([
                ('competition_id', '=', participant.competition_id.id),
                ('participant_id', '=', participant.participant_id.id),
                ('id', '!=', participant.id)
            ])
            if duplicates:
                raise ValidationError(_('A participant can only register once per competition'))
    
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
    
    @api.constrains('amount_juz')
    def _check_amount_juz_limits(self):
        """Validate amount_juz is greater than zero and not exceeding 30"""
        for participant in self:
            if participant.amount_juz <= 0:
                raise ValidationError(_('Amount (Juz\') must be greater than zero'))
            
            if participant.amount_juz > 30:
                raise ValidationError(_('Amount (Juz\') cannot exceed 30 (total Quran parts)'))
    
    @api.constrains('registration_number', 'competition_id')
    def _check_unique_registration_number(self):
        """Ensure registration_number is unique per competition when not empty"""
        for participant in self:
            if participant.registration_number and participant.competition_id:
                duplicates = self.search([
                    ('competition_id', '=', participant.competition_id.id),
                    ('registration_number', '=', participant.registration_number),
                    ('id', '!=', participant.id)
                ])
                if duplicates:
                    raise ValidationError(_('Registration number "%s" is already used in this competition') % 
                                       participant.registration_number)
    
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
                    # Convert competition_date to datetime for comparison
                    competition_datetime = fields.Datetime.to_datetime(participant.competition_id.competition_date)
                    if participant.registration_date < competition_datetime:
                        raise ValidationError(_('Registration date cannot be before competition date (%s)') % 
                                           participant.competition_id.competition_date.strftime('%Y-%m-%d'))

    # =========================== Dependencies Methods ===========================
    @api.depends('amount_juz', 'memorization_method')
    def _compute_surah_aya_from_amount_juz(self):
        """ Compute surah and ayah based on memorization amount in Juz' """
        for record in self:
            method = 2
            if record.memorization_method == 'from_baqarah':
                method = 1
            if record.memorization_method == 'from_nas':
                method = 0

            result = self.env['quran_office.ayat'].calc_surah_ayah_from_amount(method, record.amount_juz)
            record.surah = result['surah_id']
            record.ayah = result['ayah_num']
    
    # ========================= OnChange Methods =========================
    @api.onchange('participant_id')
    def _onchange_participant_id(self):
        """Auto-fill office, class, teacher, and memorization method from student"""
        if self.participant_id:
            # Auto-fill office, class, teacher
            self.office_id = self.participant_id.office_id
            self.class_id = self.participant_id.class_id
            self.teacher_id = self.participant_id.teacher_id
            if self.participant_id.birth_date:
                self.age_from_id = self.participant_id.age_from_id
                self.age_years = self.participant_id.age_years
                self.age_months = self.participant_id.age_months
                self.age_days = self.participant_id.age_days
            else:
                self.age_from_id = ''
                self.age_years = 0
                self.age_months = 0
                self.age_days = 0
            self.memorization_method = self.participant_id.memorization_method
            # Check if student has memorized full Quran (30 juz)
            if self.participant_id.is_quran_memorizer:
                self.amount_juz = 30.0

    # ========================= Action Methods =========================
    def action_confirm_participant(self):
        """Confirm participant registration"""
        self.write({'state': 'confirmed'})

    def action_mark_inappropriate(self):
        """Mark participant as participated"""
        self.write({'state': 'inappropriate'})

    def action_disqualify_participant(self):
        """Disqualify participant"""
        self.write({'state': 'disqualified'})

    def action_withdraw_participant(self):
        """Withdraw participant"""
        self.write({'state': 'withdrawn'})

    def action_reset_to_registered(self):
        """Reset participant to registered status"""
        self.write({'state': 'registered'})
