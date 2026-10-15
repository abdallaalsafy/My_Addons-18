# -*- coding: utf-8 -*-
"""
OpenEduCat Faculty Model

This module defines the faculty model for educational management system.
Faculty members are instructors/teachers who can teach subjects and manage courses.
"""

from odoo import _, api, fields, models


class OpFaculty(models.Model):
    """
    Faculty model for educational management system.
    Represents teachers/instructors who can teach subjects and manage courses.
    Inherits from res.partner for contact information and mail features.
    """
    _name = "op.faculty"
    _description = "OpenEduCat Faculty"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {"res.partner": "partner_id"}
    _parent_name = False

    # Basic fields
    partner_id = fields.Many2one(
        'res.partner', 
        'Partner',
        required=True, 
        ondelete="cascade",
        help="Related partner contact information"
    )
    

    

    active = fields.Boolean(default=True)
