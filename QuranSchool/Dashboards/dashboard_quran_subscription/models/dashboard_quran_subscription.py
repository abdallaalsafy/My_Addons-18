# -*- coding: utf-8 -*-
from odoo import _, models

GROUP_USER = 'management_quran_office_core.group_quran_office_user'


class DashboardQuranSubscription(models.AbstractModel):
    """Dashboard data for management_quran_subscription.

    Source model ``monthly.subscription`` (verified fields): subscription_month (Date, any day
    of the billed month), expected_amount / paid_amount / remaining_amount (Monetary, stored),
    currency_id (related to student currency, stored), student_id, office_id, month_name.
    Students: res.persons (is_student, status, subscription_fee, office_id).

    Currency policy: amounts are NEVER summed across currencies; every currency gets its own
    figures. ``remaining_amount`` is expected - paid, so it is a net figure (over-payments
    reduce it).
    """
    _name = 'dashboard.quran.subscription'
    _inherit = 'unified.dashboard.base'
    _description = 'Dashboard data: Quran Subscription'

    _ud_default_groups = (GROUP_USER,)

    def _ud_period_domain(self, period):
        return [
            ('subscription_month', '>=', period['month_from']),
            ('subscription_month', '<=', period['date_to']),
        ]

    def _ud_widget_subscription_kpis(self, period):
        Subscription = self.env['monthly.subscription']
        groups = Subscription._read_group(
            self._ud_period_domain(period),
            ['currency_id'],
            ['__count', 'expected_amount:sum', 'paid_amount:sum', 'remaining_amount:sum'],
        )
        multi = len(groups) > 1
        tiles = []
        for currency, count, expected, paid, remaining in groups:
            suffix = f" ({currency.name})" if multi else ""
            rate = self._ud_ratio(paid, expected)
            tiles += [
                {'label': _("Expected") + suffix, 'value': expected, 'format': 'monetary',
                 'currency': currency.name, 'tone': 'neutral',
                 'hint': _("%s subscriptions", count)},
                {'label': _("Collected") + suffix, 'value': paid, 'format': 'monetary',
                 'currency': currency.name, 'tone': 'good'},
                {'label': _("Remaining") + suffix, 'value': remaining, 'format': 'monetary',
                 'currency': currency.name, 'tone': 'warn' if remaining > 0 else 'good',
                 'hint': _("Net of over-payments")},
                {'label': _("Collection rate") + suffix, 'value': rate, 'format': 'percent',
                 'tone': 'good' if rate is not None and rate >= 100 else 'neutral'},
            ]

        # Operational exception: eligible students with no subscription record in the month of
        # the period end. Eligibility mirrors the module's own validation (active student,
        # not disconnected, has an office and a positive fee).
        month_start = period['date_to'].replace(day=1)
        billed_ids = [
            student.id for (student,) in Subscription._read_group(
                [('subscription_month', '>=', month_start),
                 ('subscription_month', '<=', period['date_to'])],
                ['student_id'])
        ]
        missing_domain = [
            ('is_student', '=', True),
            ('status', '!=', 'disconnected'),
            ('office_id', '!=', False),
            ('subscription_fee', '>', 0),
            ('id', 'not in', billed_ids),
        ]
        missing = self.env['res.persons'].search_count(missing_domain)
        if not groups and not billed_ids and not missing:
            return {'empty': True,
                    'empty_message': _("No subscriptions in the selected period.")}
        tiles.append({
            'label': _("Students without a subscription"),
            'value': missing,
            'tone': 'warn' if missing else 'good',
            'hint': _("In %s", self._ud_month_label(month_start)),
            'drill': {'name': _("Students without a subscription"),
                      'res_model': 'res.persons', 'domain': missing_domain} if missing else False,
        })
        return {'tiles': tiles}

    def _ud_widget_subscription_trend(self, period):
        months = self._ud_trend_months(period, 6)
        groups = self.env['monthly.subscription']._read_group(
            [('subscription_month', '>=', months[0]),
             ('subscription_month', '<=', period['date_to'])],
            ['subscription_month:month', 'currency_id'],
            ['expected_amount:sum', 'paid_amount:sum'],
        )
        if not groups:
            return {'empty': True, 'empty_message': _("No subscriptions in the last 6 months.")}
        currencies = sorted({currency for _month, currency, _e, _p in groups}, key=lambda c: c.id)
        multi = len(currencies) > 1
        series = []
        for currency in currencies:
            by_month = {m: paid for m, c, _e, paid in groups if c == currency}
            name = _("Collected")
            if multi:
                name = f"{name} ({currency.name})"
            series.append({
                'name': name,
                'points': [{'label': self._ud_month_label(m), 'value': by_month.get(m)}
                           for m in months],
            })
        return {
            'format': 'integer',
            'title': _("Collected amounts per month"),
            'series': series,
            'footer': _("Last 6 months ending at the period end. Months without subscriptions are left blank."),
        }

    def _ud_widget_subscription_outstanding(self, period):
        Subscription = self.env['monthly.subscription']
        domain = self._ud_period_domain(period) + [('remaining_amount', '>', 0)]
        total = Subscription.search_count(domain)
        if not total:
            return {'empty': True, 'empty_message': _("No outstanding balances in the selected period.")}
        records = Subscription.search(domain, order='remaining_amount desc, id', limit=10)
        rows = []
        for rec in records:
            rows.append({
                'student': rec.student_id.display_name,
                'month': rec.month_name,
                'office': rec.office_id.display_name or '',
                'remaining': rec.remaining_amount,
                'currency': rec.currency_id.name,
                'drill': {'name': rec.display_name, 'res_model': 'monthly.subscription',
                          'res_id': rec.id},
            })
        return {
            'columns': [
                {'key': 'student', 'label': _("Student")},
                {'key': 'month', 'label': _("Month")},
                {'key': 'office', 'label': _("Office")},
                {'key': 'remaining', 'label': _("Remaining"), 'format': 'monetary',
                 'currency_key': 'currency', 'align': 'end'},
            ],
            'rows': rows,
            'footer': _("Showing %(shown)s of %(total)s subscriptions with a remaining balance "
                        "(largest amounts first).", shown=len(rows), total=total),
        }
