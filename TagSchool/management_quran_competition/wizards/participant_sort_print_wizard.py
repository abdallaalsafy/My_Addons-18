# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ParticipantSortPrintWizard(models.TransientModel):
    _name = 'participant.sort.print.wizard'
    _description = 'Participant Sort and Print Wizard'

    # Global sorting type
    global_sort_type = fields.Selection([
        ('desc', 'Descending (Highest to Lowest)'),
        ('asc', 'Ascending (Lowest to Highest)'),
    ], 'Global Sort Type',
        default='desc',
        required=True,
        help="Apply this sort type to all selected sorting options"
    )

    # Sorting options
    sort_by_score = fields.Boolean(
        'Sort by Score',
        default=True,
        help="Sort results by score"
    )
    sort_by_juze_amount = fields.Boolean(
        'Sort by Amount Juz',
        default=True,
        help="Sort results by amount Juz"
    )

    # Additional sorting options
    sort_by_name = fields.Boolean(
        'Sort by Name',
        default=False,
        help="Sort results by student name"
    )
    sort_by_registration_number = fields.Boolean(
        'Sort by Registration Number',
        default=False,
        help="Sort results by registration number"
    )
    sort_by_office = fields.Boolean(
        'Sort by Office',
        default=False,
        help="Sort results by office name"
    )
    sort_by_class = fields.Boolean(
        'Sort by Class',
        default=False,
        help="Sort results by class name"
    )

    def get_sorted_participants(self):
        """Get selected participants from context and apply sorting"""
        # Get selected participant IDs from context
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            raise ValidationError(_('Please select participants to print.'))
        
        participants = self.env['quran.competition.participant'].browse(active_ids)
        participants = participants.sorted(key=lambda p:(
            p.student_id.name if self.sort_by_name else '',
            p.score if self.sort_by_score else 0,
            p.juze_amount if self.sort_by_juze_amount else 0,
            p.registration_number if self.sort_by_registration_number else '',
            p.office_id.name if self.sort_by_office else '',
            p.class_id.name if self.sort_by_class else ''
        ), reverse=self.global_sort_type == 'desc')
        
        return participants

    def action_print_selected_participants(self):
        """Print selected participants with chosen sorting"""
        self.ensure_one()
        
        participants = self.get_sorted_participants()
        
        if not participants:
            raise ValidationError(_('No participants found to print.'))
        
        # Return report action
        return self.env.ref('management_quran_competition.report_participant_list').report_action(
            participants.ids
        )
