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
        'Code',
        default=lambda self: _('New'),
        copy=False,
        help="Unique code for the requirement"
    )
    description = fields.Text(
        'Description',
        help="Detailed description of the requirements"
    )
    participant_nums = fields.Integer(
        'Participant Numbers',
        default=10,
        help="Number of participants allowed for this requirement"
    )
    # Age Requirements =======================================
    min_age = fields.Integer(
        'Minimum Age',
        help="Minimum age requirement for participants"
    )
    max_age = fields.Integer(
        'Maximum Age',
        help="Maximum age requirement for participants"
    )

    # Memorization Requirements ======================================
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

    # Specific Surah Requirements =====================================
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
    
    # Previous Competition Requirements =====================================
    highest_level_yet = fields.Boolean(
        'Highest Level Yet',
        default=False,
        help="Whether the participant has achieved the highest level yet"
    )
    registration_status = fields.Selection(
        [('registered', 'Previously Registered'), ('not_registered', 'Not Registered')],
        'Registration Status',
        help="Registration status for previous competitions"
    )
    required_competition_ids = fields.Many2many(
        'quran.competition',
        string='Required Competitions',
        help="Competitions that are related to this requirement"
    )
    required_tag_ids = fields.Many2many(
        'quran.competition.tag',
        string='Tags',
        help="Tags for this requirement template"
        )
    
    # Office/Class Requirements =====================================
    office_ids = fields.Many2many(
        'quran.office.office',
        string='Required Offices',
        help="Offices that must be assigned"
    )
    teacher_ids = fields.Many2many(
        'res.partner',
        domain=[('is_teacher', '=', True)],
        string='Required Teachers',
        help="Teachers that must be assigned"
    )
    
    # Custom Requirements =====================================
    custom_requirements = fields.Text(
        'Custom Requirements',
        help="Additional custom requirements"
    )
    active = fields.Boolean(
        'Active',
        default=True,
        help="If unchecked, this requirement will not be available"
    )
    
# Related competitions =====================================
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

# ========================= Builtin Functions =========================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set code if not provided"""
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('competition.requirements') or _('New')
        return super(CompetitionRequirements, self).create(vals_list)
    
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
    
# ======================= Onchange Functions ========================================
    @api.onchange('memorization_required')
    def _onchange_memorization_required(self):
        if not self.memorization_required:
            self.min_memorization_amount = 0.0
            self.max_memorization_amount = 0.0
            self.specific_surahs_required = False

    @api.onchange('specific_surahs_required')
    def _onchange_specific_surahs_required(self):
        if not self.specific_surahs_required:
            self.required_surah_ids = [(5, 0, 0)]
        else:
            self.min_memorization_amount = 0.0
            self.max_memorization_amount = 0.0

    @api.onchange('registration_status')
    def _onchange_registration_status(self):
        if not self.registration_status:
            self.required_competition_ids = [(5, 0, 0)]
            self.required_tag_ids = [(5, 0, 0)]

# ======================== Compute Functions =========================================
    @api.depends('competition_ids')
    def _compute_competition_count(self):
        """Compute number of competitions using this requirement"""
        for requirement in self:
            requirement.competition_count = len(requirement.competition_ids)
    
# ======================= Constraint Functions =========================================
    @api.constrains('min_age', 'max_age')
    def _check_age_limits(self):
        """Validate age limits"""
        for requirement in self:
            min_age = requirement.min_age
            max_age = requirement.max_age
            if (max_age != 0 or min_age != 0) and (max_age <= 0 or min_age <= 0 or (min_age > max_age)):
                raise ValidationError(_('Minimum age cannot be greater than maximum age or be negative or zero or maximum age cannot be zero or negative'))
    
    @api.constrains('min_memorization_amount', 'max_memorization_amount','memorization_required', 'specific_surahs_required')
    def _check_memorization_limits(self):
        """Validate memorization limits"""
        for requirement in self:
            min_memorization = requirement.min_memorization_amount
            max_memorization = requirement.max_memorization_amount
            if requirement.memorization_required and not requirement.specific_surahs_required and (min_memorization > max_memorization or min_memorization < 0 or max_memorization <= 0):
                raise ValidationError(_('Minimum memorization amount cannot be greater than maximum memorization amount or be negative or zero or maximum memorization amount cannot be zero or negative'))

    @api.constrains('specific_surahs_required', 'required_surah_ids','memorization_required')
    def _check_specific_surahs(self):
        """Validate specific surahs requirement"""
        for requirement in self:
            if requirement.memorization_required and requirement.specific_surahs_required and not requirement.required_surah_ids:
                raise ValidationError(_('Specific surahs are required, but no surahs are selected.'))

# ======================= Action Functions =========================================
    def action_view_related_competitions(self):
        """View competitions that use this requirement"""
        self.ensure_one()
        action = self.env.ref("management_quran_competition.action_quran_competition_view_id").read()[0]
        action['domain'] = [('requirement_id', '=', self.id)]
        action['context'] = {'default_requirement_id': self.id}
        return action

# ======================= Helper Functions ========================================= 
    
        

    
        

