# dashboard_quran_attendance

Integration addon: contributes widgets for `management_quran_attendance` to the single dashboard owned by `unified_dashboard_core`.

- Depends on: `unified_dashboard_core`, `management_quran_attendance`
- `auto_install: True` -> installed automatically once both dependencies are installed
  (also when the Core is installed after the business addon).
- Creates no menu or action; the original addon is not modified.
- Server model: `dashboard.quran.attendance` (AbstractModel inheriting `unified.dashboard.base`).
- Access: users of group `management_quran_office_core.group_quran_office_user` (managers inherit it).
  Queries run as the current user (no `sudo`), so ACLs still apply.

## Widgets
- `attendance_kpis`
- `attendance_trend`
- `attendance_classes`
- `attendance_students`

## Assumptions
Rates use filled-in study days only; absent days include excused and sick days.
