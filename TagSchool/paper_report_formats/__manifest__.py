# -*- coding: utf-8 -*-

{
    'name': 'Paper Formats Management',
    'version': '1.0',
    'category': 'Technical',
    'summary': 'Manage Paper formats for reports and documents',
    'description': """
        Paper Formats Management Module
        ==============================
        
        This module provides a centralized system for managing Paper formats
        that can be used across different reports and documents in the system.
        
        Features:
        - Create and manage custom PDF formats
        - Define page size, margins, orientation
        - Set header/footer configurations
        - Reuse formats across multiple reports
        - Easy format selection and preview
    """,
    'author': 'Abdallaalsafy',
    'website': 'https://www.facebook.com/abdalla6alsafy',
    'depends': ['base'],
    'data': [
        'reports/paper_format_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
