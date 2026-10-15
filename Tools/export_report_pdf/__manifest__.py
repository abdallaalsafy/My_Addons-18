# -*- coding: utf-8 -*-
{
    'name': 'Export Report Customization',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Add report title and orientation fields to export dialog',
    'description': """
        This module extends the export dialog to add:
        - Report Title field (text)
        - Report Orientation field (landscape/portrait)
    """,
    'author': 'TagSchool',
    'depends': ['base', 'web'],
    'data': [
        'reports/report_actions.xml',
        'reports/report_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'export_report_pdf/static/src/views/view_dialogs/export_data_dialog.xml',
            'export_report_pdf/static/src/views/view_dialogs/export_data_dialog.js',
            'export_report_pdf/static/src/js/list_controller.js',
        ],
    },
    'installable': True,
    'application': False,
}
