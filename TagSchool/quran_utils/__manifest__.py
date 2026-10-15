# -*- coding: utf-8 -*-
{
    'name': 'Quran Utils',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Quran Office Utility Models and Data',
    'description': """
        Quran Utils Module
        ===================
        
        This module provides utility models and data for Quran office management:
        - Surah model for Quran chapters
        - Ayat model for Quran verses
        - Pre-loaded Quran data including surah and ayat information
    """,
    'author': 'abdallaalsafy',
    'website': 'https://www.facebook.com/abdalla6alsafy',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/quran_office.surah.csv',
        'data/quran_office.ayat.csv',
        'data/quran_office.ayat_desc.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
