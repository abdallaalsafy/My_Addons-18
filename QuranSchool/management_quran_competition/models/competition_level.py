# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class QuranCompetitionLevel(models.Model):
    _name = 'quran.competition.level'
    _description = 'Quran Competition Level'
    _order = 'required_juz desc, name'

    name = fields.Char(
        string='Level Name',
        required=True,
        help='Name of the memorization level'
    )
    competition_id = fields.Many2one(
            'quran.competition',
            string='Competition',
            required=True,
            ondelete='cascade',
            help='Competition related to this level'
        )
    required_juz = fields.Float(
        string='Required Memorization (Juz)',
        digits=(5, 2),
        help='Amount of memorized Juz required for this level'
    )
    notes = fields.Text(
            string='Notes',
            help='Additional note for this competition level'
        )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this level is active'
    )

    _sql_constraints = [
        (
            'competition_level_name_uniq',
            'unique(competition_id, name)',
            'Level name must be unique per competition!'
        ),
        (
            'competition_level_juz_uniq',
            'unique(competition_id, required_juz)',
            'Required memorization amount must be unique per competition!'
        ),
        (
            'competition_level_juz_positive',
            'check(required_juz > 0 and required_juz <= 30)',
            'Required memorization amount must be greater than zero and less than or equal to 30!'
        ),
    ]

# ============================= Builtin Methods ===============================
    @api.depends('competition_id', 'name')
    def _compute_display_name(self):
        for record in self:
            if record.competition_id:
                record.display_name = f"[{record.competition_id.name}] {record.name}"
            else:
                record.display_name = record.name