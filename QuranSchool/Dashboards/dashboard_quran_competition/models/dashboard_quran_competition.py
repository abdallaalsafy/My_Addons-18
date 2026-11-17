# -*- coding: utf-8 -*-
from odoo import _, models

GROUP_USER = 'management_quran_office_core.group_quran_office_user'


class DashboardQuranCompetition(models.AbstractModel):
    """Dashboard data for management_quran_competition.

    Source models (verified fields):
      quran.competition: competition_date, status (opening/completed/closed), participants_count
      quran.competition.participant: competition_id, state (draft/confirmed/disqualified/withdrawn),
          status (superior/successful/acceptable/precipitate), evaluation_percentage (stored),
          monetary_prize, currency_id

    Assumption: participants that are disqualified or withdrawn are excluded from the
    evaluation and prize figures. Prizes are summed per currency, never across currencies.
    """
    _name = 'dashboard.quran.competition'
    _inherit = 'unified.dashboard.base'
    _description = 'Dashboard data: Quran Competition'

    _ud_default_groups = (GROUP_USER,)

    _STATUS_ORDER = ('superior', 'successful', 'acceptable', 'precipitate')

    def _ud_competition_domain(self, period):
        return [
            ('competition_date', '>=', period['date_from']),
            ('competition_date', '<=', period['date_to']),
        ]

    def _ud_participant_domain(self, period):
        return [
            ('competition_id.competition_date', '>=', period['date_from']),
            ('competition_id.competition_date', '<=', period['date_to']),
        ]

    def _ud_widget_competition_overview(self, period):
        Competition = self.env['quran.competition']
        Participant = self.env['quran.competition.participant']
        by_status = dict(Competition._read_group(
            self._ud_competition_domain(period), ['status'], ['__count']))
        by_state = dict(Participant._read_group(
            self._ud_participant_domain(period), ['state'], ['__count']))
        competitions = sum(by_status.values())
        participants = sum(by_state.values())
        if not competitions and not participants:
            return {'empty': True,
                    'empty_message': _("No competitions in the selected period.")}
        status_labels = self._ud_selection_labels('quran.competition', 'status')
        tiles = [
            {'label': _("Competitions"), 'value': competitions, 'tone': 'neutral'},
            {'label': status_labels.get('opening', 'opening'),
             'value': by_status.get('opening', 0), 'tone': 'neutral'},
            {'label': status_labels.get('completed', 'completed'),
             'value': by_status.get('completed', 0), 'tone': 'neutral'},
            {'label': status_labels.get('closed', 'closed'),
             'value': by_status.get('closed', 0), 'tone': 'neutral'},
            {'label': _("Participants"), 'value': participants, 'tone': 'neutral'},
            {'label': _("Confirmed participants"), 'value': by_state.get('confirmed', 0),
             'tone': 'good'},
            {'label': _("Disqualified"), 'value': by_state.get('disqualified', 0),
             'tone': 'warn' if by_state.get('disqualified') else 'neutral'},
        ]
        prizes = Participant._read_group(
            self._ud_participant_domain(period) + [
                ('state', 'not in', ('disqualified', 'withdrawn')),
                ('monetary_prize', '>', 0)],
            ['currency_id'], ['monetary_prize:sum'])
        multi = len(prizes) > 1
        for currency, total in prizes:
            tiles.append({
                'label': _("Monetary prizes") + (f" ({currency.name})" if multi else ""),
                'value': total, 'format': 'monetary', 'currency': currency.name,
                'tone': 'neutral',
            })
        return {'tiles': tiles}

    def _ud_widget_competition_upcoming(self, period):
        Competition = self.env['quran.competition']
        records = Competition.search(
            [('status', '=', 'opening'), ('competition_date', '>=', period['today'])],
            order='competition_date asc, id', limit=5)
        if not records:
            return {'empty': True, 'empty_message': _("No upcoming open competitions.")}
        return {
            'columns': [
                {'key': 'name', 'label': _("Competition")},
                {'key': 'date', 'label': _("Date"), 'format': 'date'},
                {'key': 'participants', 'label': _("Participants"), 'format': 'integer',
                 'align': 'end'},
            ],
            'rows': [{
                'name': rec.display_name,
                'date': rec.competition_date and rec.competition_date.isoformat(),
                'participants': rec.participants_count,
                'drill': {'name': rec.display_name, 'res_model': 'quran.competition',
                          'res_id': rec.id},
            } for rec in records],
        }

    def _ud_widget_competition_results(self, period):
        groups = self.env['quran.competition.participant']._read_group(
            self._ud_participant_domain(period) + [
                ('status', '!=', False),
                ('state', 'not in', ('disqualified', 'withdrawn'))],
            ['status'], ['__count', 'evaluation_percentage:avg'])
        if not groups:
            return {'empty': True,
                    'empty_message': _("No evaluated participants in the selected period.")}
        labels = self._ud_selection_labels('quran.competition.participant', 'status')
        by_status = {status: (count, avg) for status, count, avg in groups}
        items = []
        for status in self._STATUS_ORDER:
            if status not in by_status:
                continue
            count, avg = by_status[status]
            items.append({
                'label': labels.get(status, status),
                'value': count,
                'secondary_text': (_("Average score %s", f"{avg:.1f}%") if avg is not None else ''),
            })
        return {'format': 'integer', 'items': items}
