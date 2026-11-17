# dashboard_quran_office_core

Integration addon: contributes widgets for `management_quran_office_core` to the single dashboard owned by `unified_dashboard_core`.

- Depends on: `unified_dashboard_core`, `management_quran_office_core`
- `auto_install: True` -> installed automatically once both dependencies are installed
  (also when the Core is installed after the business addon).
- Creates no menu or action; the original addon is not modified.
- Server model: `dashboard.quran.office_core` (AbstractModel inheriting `unified.dashboard.base`).
- Access: users of group `management_quran_office_core.group_quran_office_user` (managers inherit it).
  Queries run as the current user (no `sudo`), so ACLs still apply.

## Widgets
- `students_overview`
- `students_by_office`
- `students_levels`
- `data_gaps`

## Assumptions
Current-state widgets (ignore the period filter).
