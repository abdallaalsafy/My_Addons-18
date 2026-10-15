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
        help="Date when the competition will be held"
    )
    
    current_participants = fields.Integer(
        'Current Participants',
        compute='_compute_participants_count',
        store=True,
        help="Current number of registered participants"
    )
    
    requirement_id = fields.Many2one(
        'competition.requirements',
        string='Requirements',
        help="Requirements template for this competition"
    )
    
    judge_ids = fields.Many2many(
        'res.partner',
        'competition_judge_rel',
        'competition_id',
        'judge_id',
        string='Judges',
        domain="[('is_teacher', '=', True)]",
        help="Judges for evaluating participants"
    )
    
    participant_ids = fields.One2many(
        'quran.competition.participant',
        'competition_id',
        string='Participants',
        help="Participants in this competition"
    )
    
    state = fields.Selection([
        ('opening', 'Opening'),
        ('completed', 'Completed'),
    ], 'Status',
        default='opening',
        required=True,
        help="Current status of the competition"
    )

    description = fields.Text(
        'Description',
        help="Detailed description of the competition"
    )

    test_grade = fields.Integer(
        string='Test Grade',
        default=100,
        required=True,
        help="Student's test grade (must not exceed student grade)"
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

    def name_get(self):
        """Override name_get to show code and name"""
        result = []
        for competition in self:
            if competition.code:
                name = f"[{competition.code}] {competition.name}"
            else:
                name = competition.name
            result.append((competition.id, name))
        return result

    # =================== COMPUTE METHODS ===================
    @api.depends('participant_ids')
    def _compute_participants_count(self):
        """Compute current number of participants"""
        for competition in self:
            competition.current_participants = len(competition.participant_ids)

    # ==================== Action Methods ====================
    def action_complete_competition(self):
        """Mark competition as completed"""
        self.write({'state': 'completed'})

