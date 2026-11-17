# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QuranCompetition(models.Model):
    _name = 'quran.competition'
    _description = 'Quran Competition'
    _order = 'competition_date desc, name desc'
    _rec_name = 'name'

    name = fields.Char(
        'Competition Name',
        required=True,
        help="Name of the Quran competition"
    )
    code = fields.Char(
        'Competition Code',
        required=True,
        copy=False,
        default=lambda self: _('New'),
        readonly=True,
        help="Unique code for the competition"
    )
    competition_date = fields.Date(
        'Competition Date',
        required=True,
        default=lambda self: fields.Date.today(),
        help="Date when the competition will be held"
    )
    requirement_id = fields.Many2one(
        'competition.requirements',
        string='Requirements',
        help="Requirements template for this competition"
    )
    tag_ids = fields.Many2many(
        'quran.competition.tag',
        string='Tags',
        help="Tags for this competition"
    )
    judge_ids = fields.Many2many(
        'res.persons',
        column1='competition_id', column2='judge_id',
        relation='competition_judges_rel',
        string='Judges',
        domain="[('is_teacher', '=', True)]",
        help="Judges for evaluating participants"
    )
    participants_count = fields.Integer(
        'Current Participants',
        compute='_compute_participants_count',
        store=True,
        help="Current number of registered participants"
    )
    participants_ids = fields.One2many(
        'quran.competition.participant',
        'competition_id',
        string='Participants',
        help="Participants in this competition"
    )
    students_ids = fields.Many2many(
        'res.persons',
        string='Students',
        relation="competition_students_rel", column1="competition_id", column2="student_id",
        compute="_compute_students_of_competition",
        store=True,
        help="Students in this competition"
    )
    level_ids = fields.One2many(
        'quran.competition.level',
        'competition_id',
        string='Accepted Levels',
        help='Levels accepted in this competition'
    )
    evaluation_rule_ids = fields.One2many(
        'quran.competition.participant.result',
        'competition_id',
        string='Evaluation Rules',
        help='Score thresholds and result labels for participants'
    )
    status = fields.Selection([
        ('opening', 'Opening'),
        ('completed', 'Completed'),
        ('closed', 'Closed')
    ], 'Status',
        default='opening',
        required=True,
        help="Current status of the competition"
    )
    test_grade = fields.Integer(
        string='Test Grade',
        default=100,
        required=True,
        help="Maximum grade of the competition test."
    )
    description = fields.Text(
            'Description',
            help="Detailed description of the competition"
        )
    notes = fields.Text(
        'Notes',
        help="Additional notes for the competition"
    )

# =================== Built-in Methods ===================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate competition code"""
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('quran.competition')
        return super().create(vals_list)

    def write(self, vals):
        for competition in self:
            if competition.status == 'closed' and 'status' not in vals:
                raise ValidationError(_('Cannot modify competition in a closed state'))
        return super().write(vals)

    @api.depends('name', 'code')
    def _compute_display_name(self):
        """Compute display name for competition"""
        for competition in self:
            if competition.code:
                competition.display_name = f"[{competition.code}] {competition.name}"
            else:
                competition.display_name = competition.name

# =================== COMPUTE METHODS ===================
    @api.depends('participants_ids')
    def _compute_participants_count(self):
        """Compute current number of participants"""
        for competition in self:
            competition.participants_count = len(competition.participants_ids)

    @api.depends('participants_ids.student_id')
    def _compute_students_of_competition(self):
        for competition in self:
            competition.students_ids = competition.participants_ids.mapped('student_id')

# ==================== Action Methods ====================
    def action_view_related_participants(self):
        """View participants that use this competition"""
        self.ensure_one()
        action = self.env.ref("management_quran_competition.action_quran_competition_participant_view_id").read()[0]
        action['domain'] = [('competition_id', '=', self.id)]
        action['context'] = {'default_competition_id': self.id}
        return action

    def action_view_related_students(self):
        """View students that use this competition"""
        self.ensure_one()
        action = self.env.ref("management_quran_office_core.action_students_view_id").read()[0]
        action['domain'] = [('id', 'in', self.students_ids.ids)]
        return action


