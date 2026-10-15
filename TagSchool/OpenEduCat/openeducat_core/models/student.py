
# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from .utils import (fnc_editstring, get_birth_date_from_national_id, get_gender_from_national_id,
                     is_invalid_national_id, get_age, get_detailed_age)

class OpStudent(models.Model):
    """
    Student model for educational management system.
    Inherits from res.partner to maintain contact information and communication.
    """
    _name = "op.student"
    _description = "Student"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {"res.partner": "partner_id"}
    _order = "ref desc, name asc"

    # Partner relationship - inherits all contact fields from res.partner
    partner_id = fields.Many2one(
        'res.partner', 
        'Partner',
        required=True,
        ondelete="cascade",
        help="Related partner contact information"
    )
    

    
    # Status
    active = fields.Boolean(
        default=True,
        help="Active status of the student record"
    )






