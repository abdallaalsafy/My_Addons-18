# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CompetitionRequirements(models.Model):
    _name = 'competition.requirements'
    _description = 'Competition Requirements'
    _order = 'name asc'
    _rec_name = 'name'

    name = fields.Char(
        'Requirement Name',
        required=True,
        help="Name of the requirement template"
    )
    
    code = fields.Char(
        'Requirement Code',
        required=True,
        copy=False,
        help="Unique code for the requirement"
    )
    
    description = fields.Text(
        'Description',
        help="Detailed description of the requirements"
    )
    
    # Age Requirements
    min_age = fields.Integer(
        'Minimum Age',
        help="Minimum age requirement for participants"
    )
    
    max_age = fields.Integer(
        'Maximum Age',
        help="Maximum age requirement for participants"
    )
    
    age_required = fields.Boolean(
        'Age Required',
        default=False,
        help="Whether age check is required"
    )
    
    # Memorization Requirements
    min_memorization_amount = fields.Float(
        'Minimum Memorization (Juz)',
        digits=(5, 2),
        help="Minimum memorization amount in Juz"
    )
    
    max_memorization_amount = fields.Float(
        'Maximum Memorization (Juz)',
        digits=(5, 2),
        help="Maximum memorization amount in Juz"
    )
    
    memorization_required = fields.Boolean(
        'Memorization Required',
        default=False,
        help="Whether memorization check is required"
    )
    
    specific_surahs_required = fields.Boolean(
        'Specific Surahs Required',
        default=False,
        help="Whether specific surahs are required"
    )
    
    required_surah_ids = fields.Many2many(
        'quran_office.surah',
        'requirement_surah_rel',
        'requirement_id',
        'surah_id',
        string='Required Surahs',
        help="Surahs that must be memorized"
    )
    
    # Previous Competition Requirements
    previous_competition_required = fields.Boolean(
        'Previous Competition Required',
        default=False,
        help="Whether participation in previous competition is required"
    )
    
    previous_competition_level = fields.Selection([
        ('any', 'Any Level'),
        ('beginner', 'Beginner Level'),
        ('intermediate', 'Intermediate Level'),
        ('advanced', 'Advanced Level'),
    ], 'Previous Competition Level',
        help="Required level of previous competition"
    )
    
    previous_competition_category = fields.Selection([
        ('any', 'Any Category'),
        ('hifz_1', '1 Juz'),
        ('hifz_5', '5 Juz'),
        ('hifz_10', '10 Juz'),
        ('hifz_15', '15 Juz'),
        ('hifz_20', '20 Juz'),
        ('hifz_30', '30 Juz'),
        ('tarteel', 'Tarteel'),
        ('tajweed', 'Tajweed'),
    ], 'Previous Competition Category',
        help="Required category of previous competition"
    )
    
    previous_competition_result = fields.Selection([
        ('any', 'Any Result'),
        ('passed', 'Passed'),
        ('top_3', 'Top 3'),
        ('top_5', 'Top 5'),
        ('winner', 'Winner'),
    ], 'Previous Competition Result',
        help="Required result in previous competition"
    )
    
    # Academic Requirements
    min_grade = fields.Float(
        'Minimum Grade',
        digits=(5, 2),
        help="Minimum grade requirement"
    )
    
    grade_required = fields.Boolean(
        'Grade Required',
        default=False,
        help="Whether grade check is required"
    )
    
    # Office/Class Requirements
    office_required = fields.Boolean(
        'Office Required',
        default=False,
        help="Whether office assignment is required"
    )
    
    class_required = fields.Boolean(
        'Class Required',
        default=False,
        help="Whether class assignment is required"
    )
    
    teacher_required = fields.Boolean(
        'Teacher Required',
        default=False,
        help="Whether teacher assignment is required"
    )
    
    # Custom Requirements
    custom_requirements = fields.Text(
        'Custom Requirements',
        help="Additional custom requirements"
    )
    
    active = fields.Boolean(
        'Active',
        default=True,
        help="If unchecked, this requirement will not be available"
    )
    
    # Related competitions
    competition_ids = fields.One2many(
        'quran.competition',
        'requirement_id',
        string='Competitions',
        help="Competitions using this requirement"
    )
    
    competition_count = fields.Integer(
        'Competition Count',
        compute='_compute_competition_count',
        store=True,
        help="Number of competitions using this requirement"
    )
    
    @api.depends('competition_ids')
    def _compute_competition_count(self):
        """Compute number of competitions using this requirement"""
        for requirement in self:
            requirement.competition_count = len(requirement.competition_ids)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate requirement code"""
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('competition.requirements')
        return super().create(vals_list)
    
    def check_participant_eligibility(self, participant):
        """
        Check if participant meets all requirements
        Returns: (eligible, messages)
        """
        self.ensure_one()
        messages = []
        
        # Check age requirements
        if self.age_required:
            age = participant.participant_age or 0
            if self.min_age and age < self.min_age:
                messages.append(_("Age (%d) is below minimum required age (%d)") % (age, self.min_age))
            if self.max_age and age > self.max_age:
                messages.append(_("Age (%d) is above maximum required age (%d)") % (age, self.max_age))
        
        # Check memorization requirements
        if self.memorization_required:
            # Get participant's memorization records
            memorization_records = self.env['student.memorization'].search([
                ('student_id', '=', participant.participant_id.id)
            ])
            
            if memorization_records:
                # Get latest memorization amount
                latest_memorization = sorted(memorization_records, key=lambda x: x.memorization_amount_juz or 0, reverse=True)[0]
                memorization_amount = latest_memorization.memorization_amount_juz or 0
                
                if self.min_memorization_amount and memorization_amount < self.min_memorization_amount:
                    messages.append(_("Memorization amount (%.2f Juz) is below minimum required (%.2f Juz)") % (
                        memorization_amount, self.min_memorization_amount))
                
                if self.max_memorization_amount and memorization_amount > self.max_memorization_amount:
                    messages.append(_("Memorization amount (%.2f Juz) is above maximum required (%.2f Juz)") % (
                        memorization_amount, self.max_memorization_amount))
                
                # Check specific surahs
                if self.specific_surahs_required and self.required_surah_ids:
                    participant_surahs = set()
                    for record in memorization_records:
                        if record.memorization_surah:
                            participant_surahs.add(record.memorization_surah.id)
                    
                    required_surahs = set(self.required_surah_ids.ids)
                    missing_surahs = required_surahs - participant_surahs
                    
                    if missing_surahs:
                        missing_names = self.env['quran_office.surah'].browse(list(missing_surahs)).mapped('name')
                        messages.append(_("Missing required surahs: %s") % ', '.join(missing_names))
            else:
                messages.append(_("No memorization records found for participant"))
        
        # Check previous competition requirements
        if self.previous_competition_required:
            previous_participations = self.env['quran.competition.participant'].search([
                ('participant_id', '=', participant.participant_id.id),
                ('state', '=', 'participated')
            ])
            
            if not previous_participations:
                messages.append(_("No previous competition participation found"))
            else:
                # Check level requirement
                if self.previous_competition_level != 'any':
                    level_match = False
                    for participation in previous_participations:
                        if participation.competition_id.competition_level == self.previous_competition_level:
                            level_match = True
                            break
                    if not level_match:
                        messages.append(_("No participation in required competition level: %s") % 
                                     dict(self._fields['previous_competition_level'].selection)[self.previous_competition_level])
                
                # Check category requirement
                if self.previous_competition_category != 'any':
                    category_match = False
                    for participation in previous_participations:
                        if participation.competition_category == self.previous_competition_category:
                            category_match = True
                            break
                    if not category_match:
                        messages.append(_("No participation in required competition category: %s") % 
                                     dict(self._fields['previous_competition_category'].selection)[self.previous_competition_category])
        # Check grade requirements
        if self.grade_required and self.min_grade:
            # Get participant's latest memorization grade
            memorization_records = self.env['student.memorization'].search([
                ('student_id', '=', participant.participant_id.id)
            ])
            if memorization_records:
                latest_grade = max(record.student_grade or 0 for record in memorization_records)
                if latest_grade < self.min_grade:
                    messages.append(_("Grade (%.1f) is below minimum required (%.1f)") % (
                        latest_grade, self.min_grade))
        
        # Check office/class/teacher requirements
        if self.office_required and not participant.office_id:
            messages.append(_("Office assignment is required"))
        
        if self.class_required and not participant.class_id:
            messages.append(_("Class assignment is required"))
        
        if self.teacher_required and not participant.teacher_id:
            messages.append(_("Teacher assignment is required"))
        
        return len(messages) == 0, messages
    
    @api.constrains('min_age', 'max_age')
    def _check_age_limits(self):
        """Validate age limits"""
        for requirement in self:
            if requirement.age_required and requirement.min_age and requirement.max_age:
                if requirement.min_age > requirement.max_age:
                    raise ValidationError(_('Minimum age cannot be greater than maximum age'))
    
    @api.constrains('min_memorization_amount', 'max_memorization_amount')
    def _check_memorization_limits(self):
        """Validate memorization limits"""
        for requirement in self:
            if requirement.memorization_required and requirement.min_memorization_amount and requirement.max_memorization_amount:
                if requirement.min_memorization_amount > requirement.max_memorization_amount:
                    raise ValidationError(_('Minimum memorization cannot be greater than maximum memorization'))
    
    def name_get(self):
        """Override name_get to show code and name"""
        result = []
        for requirement in self:
            if requirement.code:
                name = f"[{requirement.code}] {requirement.name}"
            else:
                name = requirement.name
            result.append((requirement.id, name))
        return result
