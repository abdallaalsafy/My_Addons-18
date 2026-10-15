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
    sort_by_amount_juz = fields.Boolean(
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
        
        # Build sort order based on global sort type
        desc_suffix = ' desc' if self.global_sort_type == 'desc' else ' asc'
        order_parts = []
        
        # Add main sorting options
        if self.sort_by_score:
            order_parts.append(f'score{desc_suffix}')
        if self.sort_by_amount_juz:
            order_parts.append(f'amount_juz{desc_suffix}')
        
        # Add additional sorting options
        if self.sort_by_name:
            order_parts.append(f'participant_id.name{desc_suffix}')
        if self.sort_by_registration_number:
            order_parts.append(f'registration_number{desc_suffix}')
        if self.sort_by_office:
            order_parts.append(f'office_id.name{desc_suffix}')
        if self.sort_by_class:
            order_parts.append(f'class_id.name{desc_suffix}')
        
        # Apply sorting if any options selected
        if order_parts:
            order = ', '.join(order_parts)
            participants = participants.sorted(lambda p: (
                p.score or 0 if self.sort_by_score else 0,
                p.amount_juz or 0 if self.sort_by_amount_juz else 0,
                p.participant_id.name or '' if self.sort_by_name else '',
                p.registration_number or '' if self.sort_by_registration_number else '',
                p.office_id.name or '' if self.sort_by_office else '',
                p.class_id.name or '' if self.sort_by_class else ''
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
