# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from ..models.constants import _STATE_SELECTION


class ParticipantFilterWizard(models.TransientModel):
    _name = 'participant.filter.wizard'
    _inherit = ['school.organization.mixin']
    _description = 'Advanced Participant Filter Wizard'

    # Global sorting
    global_sort_type = fields.Selection([
        ('asc', 'Ascending (Lowest to Highest)'),
        ('desc', 'Descending (Highest to Lowest)'),
    ], 'Global Sort Type',
        default='asc',
        required=True,
        help="Apply the same sort direction to all selected sorting options"
    )

    sort_by_percentage = fields.Boolean(
        'Sort by Percentage',
        help="Sort results by percentage"
    )
    sort_by_juze_amount = fields.Boolean(
        'Sort by Amount Juz',
        help="Sort results by amount Juz"
    )
    sort_by_name = fields.Boolean(
        'Sort by Name',
        help="Sort results by student name"
    )
    sort_by_registration_number = fields.Boolean(
        'Sort by Registration Number',
        help="Sort results by registration number"
    )
    sort_by_office = fields.Boolean(
        'Sort by Office',
        help="Sort results by office name"
    )
    sort_by_class = fields.Boolean(
        'Sort by Class',
        help="Sort results by class name"
    )

    # Competition filtering
    competition_id = fields.Many2one(
        'quran.competition',
        'Competition',
        help="Filter by competition or leave empty to include all"
    )

    # Filter ===============================================
    student_id = fields.Many2one(
        'res.persons',
        'Student',
        domain="[('is_student', '=', True)]",
        help="Filter by student or leave empty to include all"
    )
    has_office = fields.Selection([
        ('with_office', 'Has Office'),
        ('without_office', 'Without Office'),
    ], 'Office Filter')
    has_class = fields.Selection([
        ('with_class', 'Has Class'),
        ('without_class', 'Without Class'),
    ], 'Class Filter')
    has_teacher = fields.Selection([
        ('with_teacher', 'Has Teacher'),
        ('without_teacher', 'Without Teacher'),
    ], 'Teacher Filter')
    state = fields.Selection(_STATE_SELECTION, 'State')
    registration_number = fields.Char(
        'Registration Number',
        help="Filter by registration number or leave empty to include all"
    )
    has_registration_number = fields.Selection([
        ('with_registration', 'Has Registration Number'),
        ('without_registration', 'Without Registration Number'),
    ], 'Registration Number Filter')
    percentage_filter_type = fields.Selection([
        ('equals', 'Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('between', 'Between'),
    ], 'Percentage Filter Type')
    percentage_value = fields.Float(
        'Percentage Value',
        help="Percentage value for filtering"
    )
    percentage_min = fields.Float(
        'Min Percentage',
        help="Minimum percentage for between filter"
    )
    percentage_max = fields.Float(
        'Max Percentage',
        help="Maximum percentage for between filter"
    )
    juz_filter_type = fields.Selection([
        ('equals', 'Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('between', 'Between'),
    ], 'Juz Filter Type')
    juz_value = fields.Float(
        'Juz Value',
        help="Juz value for filtering"
    )
    juz_min = fields.Float(
        'Min Juz',
        help="Minimum juz for between filter"
    )
    juz_max = fields.Float(
        'Max Juz',
        help="Maximum juz for between filter"
    )
    memorization_method = fields.Selection([
        ('from_baqarah', 'From Baqarah'),
        ('from_nas', 'From Nas'),
        ('mixed', 'Mixed'),
    ], 'Memorization Method')

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
    

    # ========================= Onchange Methods =========================
    # Override the onchange methods from SchoolOrganizationMixin to avoid clearing fields in the wizard context
    def _onchange_office_id(self):
        pass
    def _onchange_class_id(self):
        pass
    def _onchange_teacher_id(self):
        pass

            
    def _get_sort_key(self,participant=None):
        """Build the sorting key for the selected options."""
        order = ""
        keys = []
        if self.sort_by_name:
            order += f"student_id {self.global_sort_type},"
            if participant:
                keys.append(participant.student_id.name or '')
        if self.sort_by_percentage:
            order += f"evaluation_percentage {self.global_sort_type},"
            if participant:
                keys.append(participant.evaluation_percentage or 0.0)
        if self.sort_by_juze_amount:
            order += f"juze_amount {self.global_sort_type},"
            if participant:
                keys.append(participant.juze_amount or 0.0)
        if self.sort_by_registration_number:
            order += f"registration_number {self.global_sort_type},"
            if participant:
                keys.append(participant.registration_number or '')
        if self.sort_by_office:
            order += f"office_id {self.global_sort_type},"
            if participant:
                keys.append(participant.office_id.name or '')
        if self.sort_by_class:
            order += f"class_id {self.global_sort_type},"
            if participant:
                keys.append(participant.class_id.name or '')
        return order.rstrip(','),tuple(keys)

    def calculate_filtered_participants(self):
        """Compute filtered participants based on all criteria"""
        wizard = self
        domain = []

        # Competition filtering
        if wizard.competition_id:
            domain.append(('competition_id', '=', wizard.competition_id.id))

        # Student filtering
        if wizard.student_id:
            domain.append(('student_id', '=', wizard.student_id.id))

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
        if wizard.percentage_filter_type == 'equals':
            domain.append(('evaluation_percentage', '=', wizard.percentage_value))
        elif wizard.percentage_filter_type == 'greater_than':
            domain.append(('evaluation_percentage', '>', wizard.percentage_value))
        elif wizard.percentage_filter_type == 'less_than':
            domain.append(('evaluation_percentage', '<', wizard.percentage_value))
        elif wizard.percentage_filter_type == 'between':
            domain.append(('evaluation_percentage', '>=', wizard.percentage_min))
            domain.append(('evaluation_percentage', '<=', wizard.percentage_max))

        # Amount Juz filtering
        if wizard.juz_filter_type == 'equals':
            domain.append(('juze_amount', '=', wizard.juz_value))
        elif wizard.juz_filter_type == 'greater_than':
            domain.append(('juze_amount', '>', wizard.juz_value))
        elif wizard.juz_filter_type == 'less_than':
            domain.append(('juze_amount', '<', wizard.juz_value))
        elif wizard.juz_filter_type == 'between':
            domain.append(('juze_amount', '>=', wizard.juz_min))
            domain.append(('juze_amount', '<=', wizard.juz_max))

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
        orders = self._get_sort_key()[0]
        records = self.calculate_filtered_participants()
        if not records:
            raise ValidationError(_('No participants found matching the criteria.'))

        view_form = self.env.ref('management_quran_competition.quran_competition_participant_form_view').id
        view_list = self.env.ref('management_quran_competition.quran_competition_participant_tree_view').id
        return {
            'name': _('Filtered Participants'),
            'type': 'ir.actions.act_window',
            'res_model': 'quran.competition.participant',
            'view_mode': 'list',
            'views': [(view_list, 'list'), (view_form, 'form')],
            'domain': [('id', 'in', records.ids)],
            'context': {'main_search_order': orders},
        }

    def action_print_results(self):
        """Print filtered or selected participants report"""
        self.ensure_one()
        records = self.calculate_filtered_participants().sorted(key=lambda p: self._get_sort_key(p)[1], reverse=self.global_sort_type == 'desc')

        if not records:
            raise ValidationError(_('No participants found matching the criteria.'))

        return self.env.ref('management_quran_competition.report_participant_list').report_action(
            records.ids
        )
