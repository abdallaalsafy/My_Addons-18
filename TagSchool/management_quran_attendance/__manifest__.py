{
    "name": "Quran Attendance Management",
    'version': '18.0.1.0.0',
    'category': 'Education',
    'sequence': 3,
    'summary': 'Manage Quran Attendance and Participants',
    'complexity': "easy",
    'author': 'Abdallaalsafy',
    'website': 'https://www.facebook.com/abdalla6alsafy',
    'depends': ['base', 'management_quran_office_core'],
    "data": [
        "security/ir.model.access.csv",
        "wizards/attendance_register_date_wizard_view.xml",
        "views/attendance_register_view.xml",
        "views/holiday_policy_views.xml",
        "views/holiday_days_views.xml",
        "views/res_config_settings_views.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # "management_quran_attendance/static/src/js/attendance_group_renderer.js",
            # "management_quran_attendance/static/src/xml/attendance_group_renderer.xml",
        ],
    },
    "installable": True,
    "application": False,
}