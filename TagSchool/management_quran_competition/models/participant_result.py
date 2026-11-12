# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from .participant import QuranCompetitionParticipant

class QuranCompetitionParticipantResult(models.Model):
    _name = 'quran.competition.participant.result'
    _description = 'Quran Competition Participant Result'
    _order = 'percentage desc, name'

    name = fields.Char(
        string='Result Name',
        required=True,
        help='Name of the evaluation result, such as Superior or Successful'
    )
    competition_id = fields.Many2one(
        'quran.competition',
        string='Competition',
        required=True,
        ondelete='cascade',
        help='Competition where this evaluation rule applies'
    )
    result_status = fields.Selection(QuranCompetitionParticipant._STATUS_SELECTION, string='Evaluation Status', required=True, default='successful',
        help='Classification assigned after evaluating the final score'
    )
    percentage = fields.Float(
        string='Percentage',
        digits=(5, 2),
        help='Score percentage for this result'
    )
    notes = fields.Text(
        string='Notes',
        help='Additional note for this evaluation result'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this evaluation rule is active'
    )

    _sql_constraints = [
        (
            'competition_result_name_uniq',
            'unique(competition_id, name)',
            'Result name must be unique for the same competition!'
        ),
        (
            'competition_result_percentage_uniq',
            'unique(competition_id, percentage)',
            'Percentage must be unique for the same competition!'
        ),
        (
            'competition_result_percentage_positive',
            'check(percentage >= 0 and percentage <= 100)',
            'Percentage must be greater than or equal to zero and less than or equal to 100!'
        ),
    ]

# ============================= Builtin Functions ===============================
    def name_get(self):
        result = []
        for record in self:
            label = record.name
            if record.competition_id:
                label = f"[{record.competition_id.name}] {record.name}"
            result.append((record.id, label))
        return result
    
# ============================= Custom Methods ===============================
    @api.model
    def get_rule_for_percentage(self, competition, percentage):
        if not competition:
            return self.browse()
        rules = competition.evaluation_rule_ids.filtered(lambda r: r.active)
        for rule in rules.sorted('percentage', reverse=True):
            if rule.percentage == percentage:
                return rule
        return self.browse()

    
