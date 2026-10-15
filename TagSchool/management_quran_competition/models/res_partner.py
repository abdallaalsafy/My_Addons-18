# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    # Competition participant count for students
    participant_count = fields.Integer(
        'Competition Participation Count',
        compute='_compute_participant_count',
        help="Number of competition participations for this student (only shown for students)"
    )

    def _compute_participant_count(self):
        """
        Compute the number of competition participations for this student (only for students)
        """
        for record in self:
            if record.is_student:
                # Count competition participants where this partner is the participant
                participants = self.env['quran.competition.participant'].search([('participant_id', '=', record.id)])
                record.participant_count = len(participants)
            else:
                record.participant_count = 0

    def action_view_participants(self):
        """View competition participations of this student"""
        self.ensure_one()
        name = _('Competition Participations of %s') % self.name
        domain = [('participant_id', '=', self.id)]
        
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'quran.competition.participant',
            'view_mode': 'list,form',
            'domain': domain,
            'context': { 
                'default_participant_id': self.id,
            }
        }
