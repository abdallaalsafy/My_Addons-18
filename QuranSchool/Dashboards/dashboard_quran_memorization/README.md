# dashboard_quran_memorization

Integration addon: contributes widgets for `management_quran_memorization` to the single dashboard owned by `unified_dashboard_core`.

- Depends on: `unified_dashboard_core`, `management_quran_memorization`
- `auto_install: True` -> installed automatically once both dependencies are installed
  (also when the Core is installed after the business addon).
- Creates no menu or action; the original addon is not modified.
- Server model: `dashboard.quran.memorization` (AbstractModel inheriting `unified.dashboard.base`).
- Access: users of group `management_quran_office_core.group_quran_office_user` (managers inherit it).
  Queries run as the current user (no `sudo`), so ACLs still apply.

## Widgets
- `memorization_kpis`
- `memorization_trend`
- `memorization_by_teacher`

## Assumptions
Grades are weighted by each test's maximum grade; `juze_amount` is not aggregated per month (it is a cumulative position).
