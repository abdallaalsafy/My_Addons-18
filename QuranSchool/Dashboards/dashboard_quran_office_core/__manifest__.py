# -*- coding: utf-8 -*-
{
    'name': 'Dashboard: Quran Office Core',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Students, offices, classes and memorization-level widgets for the unified dashboard.',
    'author': 'Abdallaalsafy',
    'depends': ['unified_dashboard_core', 'management_quran_office_core'],
    'data': [
            'views/dashboard_views.xml',
        ],
    'assets': {
        'web.assets_backend': [
            'dashboard_quran_office_core/static/src/js/widgets.js',
        ],
    },
    # Installed automatically once BOTH dependencies are installed (Odoo auto_install semantics).
    'auto_install': True,
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
