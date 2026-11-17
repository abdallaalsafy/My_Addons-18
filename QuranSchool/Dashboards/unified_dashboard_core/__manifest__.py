# -*- coding: utf-8 -*-
{
    'name': 'Unified Dashboard Core',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'One central dashboard; business addons contribute widgets through integration addons.',
    'description': """
Unified Dashboard Core
======================
Owns the single dashboard client action, the OWL shell, the shared period filter and
the widget/section registries. It does NOT depend on any business addon: integration
addons (``dashboard_*``) register their widgets into the registries.
    """,
    'author': 'Abdallaalsafy',
    'depends': ['web'],
    'data': [
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'unified_dashboard_core/static/src/scss/dashboard.scss',
            'unified_dashboard_core/static/src/js/*.js',
            'unified_dashboard_core/static/src/xml/*.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
