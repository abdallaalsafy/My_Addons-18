# -*- coding: utf-8 -*-
{
    'name': 'Management Quran Subscription',
    'version': '18.0.0.0',
    'summary': 'Manage student subscriptions in Quran offices',
    'description': """
        Quran Subscription Management Module
        ====================================
        
        This module provides comprehensive subscription management for students 
        in Quran offices, including:
        
        * Subscription plans and pricing
        * Payment tracking and billing
        * Subscription periods and renewals
        * Discount management
        * Payment methods and schedules
        * Subscription reports and analytics
        
        Dependencies:
        * management_quran_office_core (for student and office data)
    """,
    'author': 'Your Name',
    'website': 'https://www.facebook.com/abdalla6alsafy',
    'category': 'Education',
    'depends': ['management_quran_office_core', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/subscription_data.xml',
        'wizards/batch_subscription_wizard_view.xml',
        'views/subscription_view.xml',
        'views/res_partner_view.xml',
        'reports/subscription_report.xml',
        'reports/subscription_receipt_report.xml',
        'reports/subscription_report_actions.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'sequence': 2,
}
