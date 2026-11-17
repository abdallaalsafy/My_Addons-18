# -*- coding: utf-8 -*-
{
    'name': 'Dashboard: Quran Memorization',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Memorization follow-up widgets for the unified dashboard.',
    'author': 'Abdallaalsafy',
    'depends': ['unified_dashboard_core', 'management_quran_memorization'],
    'assets': {
        'web.assets_backend': [
            'dashboard_quran_memorization/static/src/js/widgets.js',
        ],
    },
    'auto_install': True,
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
