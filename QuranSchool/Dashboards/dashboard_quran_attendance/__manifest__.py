# -*- coding: utf-8 -*-
{
    'name': 'Dashboard: Quran Attendance',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Attendance and absence widgets for the unified dashboard.',
    'author': 'Abdallaalsafy',
    'depends': ['unified_dashboard_core', 'management_quran_attendance'],
    'assets': {
        'web.assets_backend': [
            'dashboard_quran_attendance/static/src/js/widgets.js',
        ],
    },
    'auto_install': True,
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
