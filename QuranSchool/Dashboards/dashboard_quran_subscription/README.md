# dashboard_quran_subscription

Integration addon: contributes widgets for `management_quran_subscription` to the single dashboard owned by `unified_dashboard_core`.

- Depends on: `unified_dashboard_core`, `management_quran_subscription`
- `auto_install: True` -> installed automatically once both dependencies are installed
  (also when the Core is installed after the business addon).
- Creates no menu or action; the original addon is not modified.
- Server model: `dashboard.quran.subscription` (AbstractModel inheriting `unified.dashboard.base`).
- Access: users of group `management_quran_office_core.group_quran_office_user` (managers inherit it).
  Queries run as the current user (no `sudo`), so ACLs still apply.

## Widgets
- `subscription_kpis`
- `subscription_trend`
- `subscription_outstanding`

## Assumptions
Amounts are never summed across currencies. `remaining_amount` is net of over-payments.
