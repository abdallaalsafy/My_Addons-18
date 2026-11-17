# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ResPersonsInherit(models.Model):
    _inherit = 'res.persons'


    participant_ids = fields.One2many(
        'quran.competition.participant',
        'student_id',
        string='Competition Participations',
        help="Competition participations of this student"
    )
    competition_ids = fields.Many2many(
        'quran.competition',
        column1='student_id', column2='competition_id',
        relation='competition_participants_rel',
        compute='_compute_competition_ids', store=True,
        string='Competitions Participated',
        help="Competitions this student has participated in"
    )

    # Competition participant count for students
    participant_count = fields.Integer(
        'Competition Participation Count',
        compute='_compute_participant_count',
        help="Number of competition participations for this student (only shown for students)"
    )

    @api.depends('participant_ids', 'participant_ids.competition_id')
    def _compute_competition_ids(self):
        """Compute the competitions this student has participated in"""
        for record in self:
            record.competition_ids = record.participant_ids.mapped('competition_id')

    def _compute_participant_count(self):
        """Compute the number of competition participations for this student (only for students)"""
        for record in self:
            record.participant_count = len(record.participant_ids)

    def action_view_participants(self):
        """View competition participations of this student"""
        self.ensure_one()
        name = _('Competition Participations of %s') % self.name
        domain = [('student_id', '=', self.id)]
        
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'quran.competition.participant',
            'view_mode': 'list,form',
            'domain': domain,
            'context': { 
                'default_student_id': self.id,
            }
        }
