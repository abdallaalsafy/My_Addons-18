# -*- coding: utf-8 -*-
"""Shared server-side contract for dashboard integration addons.

An integration addon defines an AbstractModel that inherits ``unified.dashboard.base``
and implements one method per widget named ``_ud_widget_<widget_key>(self, period)``.

Security model
--------------
* The only public entry point is :meth:`get_widget_data`; widget methods are private.
* Every widget key must be listed in ``_ud_widget_groups`` (or covered by
  ``_ud_default_groups``). The user must belong to at least one listed group, otherwise
  an ``AccessError`` is raised.
* Widget methods run with the *current user's* environment (no ``sudo``), so ACLs and
  record rules of the underlying business models still apply.
"""
import logging
import re
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import format_date

_logger = logging.getLogger(__name__)

_WIDGET_KEY_RE = re.compile(r'^[a-z][a-z0-9_]{0,63}$')
_PRESETS = ('this_month', 'last_month', 'last_3_months', 'this_year', 'custom')
_MAX_CUSTOM_DAYS = 366 * 5


class UnifiedDashboardBase(models.AbstractModel):
    _name = 'unified.dashboard.base'
    _description = 'Unified Dashboard Base (widget data contract)'

    # {widget_key: ('module.group_xmlid', ...)}; any one group is enough.
    _ud_widget_groups = {}
    # Used for widget keys not listed above. Empty tuple = every internal user.
    _ud_default_groups = ()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    @api.model
    def get_widget_data(self, widget_key, filters=None):
        if not isinstance(widget_key, str) or not _WIDGET_KEY_RE.match(widget_key):
            raise UserError(_("Invalid dashboard widget."))
        
        method = getattr(self, '_ud_widget_' + widget_key, None)
        if method is None:
            raise UserError(_("Unknown dashboard widget."))
        
        self._ud_check_access(widget_key)
        period = self._ud_resolve_period(filters)
        try:
            payload = method(period)
        except (AccessError, UserError):
            raise
        except Exception:
            _logger.exception("Dashboard widget %s.%s failed", self._name, widget_key)
            raise UserError(_("This widget could not be computed. Please check the server log."))
        payload = dict(payload or {})
        payload.setdefault('empty', False)
        payload['period'] = {
            'from': fields.Date.to_string(period['date_from']),
            'to': fields.Date.to_string(period['date_to']),
        }
        return payload

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------
    @api.model
    def _ud_check_access(self, widget_key):
        groups = self._ud_widget_groups.get(widget_key, self._ud_default_groups)
        if not groups:
            return
        user = self.env.user
        if not any(user.has_group(xmlid) for xmlid in groups):
            raise AccessError(_("You are not allowed to see this widget."))

    # ------------------------------------------------------------------
    # Period helpers (all dates computed in the user's timezone via context_today)
    # ------------------------------------------------------------------
    @api.model
    def _ud_resolve_period(self, filters):
        filters = filters if isinstance(filters, dict) else {}
        today = fields.Date.context_today(self)
        preset = filters.get('preset') or 'this_month'
        if preset not in _PRESETS:
            raise UserError(_("Invalid period."))
        month_start = today.replace(day=1)
        if preset == 'this_month':
            date_from, date_to = month_start, today
        elif preset == 'last_month':
            date_from = month_start - relativedelta(months=1)
            date_to = month_start - timedelta(days=1)
        elif preset == 'last_3_months':
            date_from, date_to = month_start - relativedelta(months=2), today
        elif preset == 'this_year':
            date_from, date_to = today.replace(month=1, day=1), today
        else:
            date_from = fields.Date.to_date(filters.get('date_from'))
            date_to = fields.Date.to_date(filters.get('date_to'))
            if not date_from or not date_to:
                raise UserError(_("Please choose both dates of the custom period."))
            if date_from > date_to:
                raise UserError(_("The start date must not be after the end date."))
            if (date_to - date_from).days > _MAX_CUSTOM_DAYS:
                raise UserError(_("The custom period is too long."))
        return {
            'preset': preset,
            'today': today,
            'date_from': date_from,
            'date_to': date_to,
            # Month-granular records (dated on any day of a month) use these bounds.
            'month_from': date_from.replace(day=1),
        }

    @api.model
    def _ud_trend_months(self, period, count=6):
        """First days of the ``count`` months ending with the month of the period end."""
        last = period['date_to'].replace(day=1)
        return [last - relativedelta(months=i) for i in range(count - 1, -1, -1)]

    @api.model
    def _ud_month_label(self, month_start):
        return format_date(self.env, month_start, date_format='MMM yyyy')

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------
    @api.model
    def _ud_selection_labels(self, model_name, field_name):
        field = self.env[model_name]._fields[field_name]
        return dict(field._description_selection(self.env))

    @api.model
    def _ud_ratio(self, numerator, denominator):
        """Percentage or None when the denominator is not positive (never fake a 0 %)."""
        if not denominator or denominator <= 0:
            return None
        return round(numerator * 100.0 / denominator, 1)
