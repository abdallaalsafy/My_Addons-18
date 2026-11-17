# -*- coding: utf-8 -*-
{
    'name': 'Management Quran Subscription',
    'version': '18.0.1.0.0',
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
    'author': 'abdallaalsafy',
    'website': 'https://www.facebook.com/abdalla6alsafy',
    'category': 'Education',
    'depends': ['management_quran_office_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_actions_server.xml',
        'wizards/batch_subscription_wizard_view.xml',
        'views/subscription_view.xml',
        'views/res_persons_view.xml',
        'reports/subscription_report.xml',
        'reports/subscription_receipt_report.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/monthly_subscription.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'sequence': 2,
}
