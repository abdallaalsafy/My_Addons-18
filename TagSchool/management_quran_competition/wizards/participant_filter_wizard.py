# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ParticipantFilterWizard(models.TransientModel):
    _name = 'participant.filter.wizard'
    _description = 'Advanced Participant Filter Wizard'

    # Competition filtering
    competition_id = fields.Many2one(
        'quran.competition',
        'Competition',
        help="Filter by competition or leave empty to include all"
    )

    # Student filtering
    participant_id = fields.Many2one(
        'res.partner',
        'Student',
        domain="[('is_student', '=', True)]",
        help="Filter by student or leave empty to include all"
    )

    # Office filtering
    office_id = fields.Many2one(
        'quran.office.office',
        'Office',
        help="Filter by office or leave empty to include all"
    )
    has_office = fields.Selection([
        ('with_office', 'Has Office'),
        ('without_office', 'Without Office'),
    ], 'Office Filter')

    # Class filtering
    class_id = fields.Many2one(
        'quran_office.class',
        'Class',
        domain="[('office_id', '=?', office_id)]",
        help="Filter by class or leave empty to include all"
    )
    has_class = fields.Selection([
        ('with_class', 'Has Class'),
        ('without_class', 'Without Class'),
    ], 'Class Filter')

    # Teacher filtering
    teacher_id = fields.Many2one(
        'res.partner',
        'Teacher',
        domain="[('is_teacher', '=', True)]",
        help="Filter by teacher or leave empty to include all"
    )
    has_teacher = fields.Selection([
        ('with_teacher', 'Has Teacher'),
        ('without_teacher', 'Without Teacher'),
    ], 'Teacher Filter')

    # Status filtering
    state = fields.Selection([
        ('registered', 'Registered'),
        ('confirmed', 'Confirmed'),
        ('inappropriate', 'Participated'),
        ('disqualified', 'Disqualified'),
        ('withdrawn', 'Withdrawn'),
    ], 'Status')

    # Registration number filtering
    registration_number = fields.Char(
        'Registration Number',
        help="Filter by registration number or leave empty to include all"
    )
    has_registration_number = fields.Selection([
        ('with_registration', 'Has Registration Number'),
        ('without_registration', 'Without Registration Number'),
    ], 'Registration Number Filter')

    # Score filtering
    score_filter_type = fields.Selection([
        ('equals', 'Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('between', 'Between'),
    ], 'Score Filter Type')
    score_value = fields.Float(
        'Score Value',
        help="Score value for filtering"
    )
    score_min = fields.Float(
        'Min Score',
        help="Minimum score for between filter"
    )
    score_max = fields.Float(
        'Max Score',
        help="Maximum score for between filter"
    )

    # Amount Juz filtering
    amount_juz_filter_type = fields.Selection([
        ('equals', 'Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('between', 'Between'),
    ], 'Amount Juz Filter Type')
    amount_juz_value = fields.Float(
        'Amount Juz Value',
        help="Amount Juz value for filtering"
    )
    amount_juz_min = fields.Float(
        'Min Amount Juz',
        help="Minimum amount Juz for between filter"
    )
    amount_juz_max = fields.Float(
        'Max Amount Juz',
        help="Maximum amount Juz for between filter"
    )

    # Memorization method filtering
    memorization_method = fields.Selection([
        ('from_baqarah', 'From Baqarah'),
        ('from_nas', 'From Nas'),
        ('mixed', 'Mixed'),
    ], 'Memorization Method')

    # Registration date filtering
    registration_date_from = fields.Date(
        'Registration Date From',
        help="Filter participants registered from this date"
    )
    registration_date_to = fields.Date(
        'Registration Date To',
        help="Filter participants registered to this date"
    )

    # Prize filtering
    has_monetary_prize = fields.Selection([
        ('with_monetary', 'Has Monetary Prize'),
        ('without_monetary', 'Without Monetary Prize'),
    ], 'Monetary Prize Filter')
    
    has_in_kind_prize = fields.Selection([
        ('with_in_kind', 'Has In-Kind Prize'),
        ('without_in_kind', 'Without In-Kind Prize'),
    ], 'In-Kind Prize Filter')

    # Competition date filtering
    competition_date_from = fields.Date(
        'Competition Date From',
        help="Filter competitions from this date"
    )
    competition_date_to = fields.Date(
        'Competition Date To',
        help="Filter competitions to this date"
    )

    
    def calculate_filtered_participants(self):
        """Compute filtered participants based on all criteria"""
        wizard = self
        domain = []

        # Competition filtering
        if wizard.competition_id:
            domain.append(('competition_id', '=', wizard.competition_id.id))

        # Student filtering
        if wizard.participant_id:
            domain.append(('participant_id', '=', wizard.participant_id.id))

        # Office filtering
        if wizard.has_office == 'with_office':
            domain.append(('office_id', '!=', False))
        elif wizard.has_office == 'without_office':
            domain.append(('office_id', '=', False))
        elif wizard.office_id:
            domain.append(('office_id', '=', wizard.office_id.id))

        # Class filtering
        if wizard.has_class == 'with_class':
            domain.append(('class_id', '!=', False))
        elif wizard.has_class == 'without_class':
            domain.append(('class_id', '=', False))
        elif wizard.class_id:
            domain.append(('class_id', '=', wizard.class_id.id))

        # Teacher filtering
        if wizard.has_teacher == 'with_teacher':
            domain.append(('teacher_id', '!=', False))
        elif wizard.has_teacher == 'without_teacher':
            domain.append(('teacher_id', '=', False))
        elif wizard.teacher_id:
            domain.append(('teacher_id', '=', wizard.teacher_id.id))

        # Status filtering
        if wizard.state:
            domain.append(('state', '=', wizard.state))

        # Registration number filtering
        if wizard.has_registration_number == 'with_registration':
            domain.append(('registration_number', '!=', False))
        elif wizard.has_registration_number == 'without_registration':
            domain.append(('registration_number', '=', False))
        elif wizard.registration_number:
            domain.append(('registration_number', 'ilike', wizard.registration_number))

        # Score filtering
        if wizard.score_filter_type == 'equals':
            domain.append(('score', '=', wizard.score_value))
        elif wizard.score_filter_type == 'greater_than':
            domain.append(('score', '>', wizard.score_value))
        elif wizard.score_filter_type == 'less_than':
            domain.append(('score', '<', wizard.score_value))
        elif wizard.score_filter_type == 'between':
            domain.append(('score', '>=', wizard.score_min))
            domain.append(('score', '<=', wizard.score_max))

        # Amount Juz filtering
        if wizard.amount_juz_filter_type == 'equals':
            domain.append(('amount_juz', '=', wizard.amount_juz_value))
        elif wizard.amount_juz_filter_type == 'greater_than':
            domain.append(('amount_juz', '>', wizard.amount_juz_value))
        elif wizard.amount_juz_filter_type == 'less_than':
            domain.append(('amount_juz', '<', wizard.amount_juz_value))
        elif wizard.amount_juz_filter_type == 'between':
            domain.append(('amount_juz', '>=', wizard.amount_juz_min))
            domain.append(('amount_juz', '<=', wizard.amount_juz_max))

        # Memorization method filtering
        if wizard.memorization_method:
            domain.append(('memorization_method', '=', wizard.memorization_method))

        # Registration date filtering
        if wizard.registration_date_from:
            domain.append(('registration_date', '>=', wizard.registration_date_from))
        if wizard.registration_date_to:
            domain.append(('registration_date', '<=', wizard.registration_date_to))

        # Prize filtering
        if wizard.has_monetary_prize == 'with_monetary':
            domain.append(('monetary_prize', '>', 0))
        elif wizard.has_monetary_prize == 'without_monetary':
            domain.append(('monetary_prize', '=', 0))
            
        if wizard.has_in_kind_prize == 'with_in_kind':
            domain.append(('in_kind_prize', '!=', False))
        elif wizard.has_in_kind_prize == 'without_in_kind':
            domain.append(('in_kind_prize', '=', False))

        # Competition date filtering
        if wizard.competition_date_from or wizard.competition_date_to:
            competition_domain = []
            if wizard.competition_date_from:
                competition_domain.append(('competition_date', '>=', wizard.competition_date_from))
            if wizard.competition_date_to:
                competition_domain.append(('competition_date', '<=', wizard.competition_date_to))
            
            if competition_domain:
                competitions = self.env['quran.competition'].search(competition_domain)
                domain.append(('competition_id', 'in', competitions.ids))

        # Get filtered participants
        participants = self.env['quran.competition.participant'].search(domain)
        
        return participants

    def action_show_filter_participants(self):
        """Filter participants and show results"""
        self.ensure_one()
        view_form = self.env.ref('management_quran_competition.quran_competition_participant_form_view').id
        view_list = self.env.ref('management_quran_competition.quran_competition_participant_tree_view').id
        return {
            'name': _('Filtered Participants'),
            'type': 'ir.actions.act_window',
            'res_model': 'quran.competition.participant',
            'view_mode': 'list',
            'views': [(view_list, 'list'), (view_form, 'form')],
            'domain': [('id', 'in', self.calculate_filtered_participants().ids)],
            'context': {}
        }

    def action_print_results(self):
        """Print filtered participants report"""
        self.ensure_one()
        records = self.calculate_filtered_participants()

        if not records:
            raise ValidationError(_('No participants found matching the criteria.'))

        return self.env.ref('management_quran_competition.report_participant_list').report_action(
            records.ids
        )
