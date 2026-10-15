# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QuranOffice(models.Model):
    _name = 'quran_office.office'
    _description = 'Quran Memorization Office'
    _order = 'name asc'

    name = fields.Char(
        'Office Name',
        required=True,
        help="Name of the Quran memorization office"
    )
    
    code = fields.Char(
        'Office Code',
        help="Unique code for the office"
    )
    
    description = fields.Text(
        'Description',
        help="Additional information about the office"
    )
    
    active = fields.Boolean(
        'Active',
        default=True,
        help="If unchecked, this office will not be available"
    )
    
    # Relationships
    student_ids = fields.One2many(
        'res.partner',
        'office_id',
        'Students',
        domain="[('is_student', '=', True)]",
        help="Students in this office"
    )
    
    class_ids = fields.One2many(
        'quran_office.class',
        'office_id',
        'Classes',
        help="Classes in this office"
    )
    
    student_count = fields.Integer(
        'Number of Students',
        compute='_compute_student_count',
        store=True,
        help="Total number of students in this office"
    )
    
    class_count = fields.Integer(
        'Number of Classes',
        compute='_compute_class_count',
        store=True,
        help="Total number of classes in this office"
    )

    # ================================ CONSTRAINTS ================================

    @api.constrains('code')
    def _check_unique_code(self):
        """
        Ensure office code is unique.
        """
        for office in self:
            if office.code:
                duplicates = self.search([
                    ('code', '=', office.code),
                    ('id', '!=', office.id)
                ])
                if duplicates:
                    raise ValidationError(_(
                        "Office Code must be unique! This code is already used."))

    @api.constrains('name')
    def _check_unique_name(self):
        """
        Ensure office name is unique.
        """
        for office in self:
            if office.name:
                duplicates = self.search([
                    ('name', '=', office.name),
                    ('id', '!=', office.id)
                ])
                if duplicates:
                    raise ValidationError(_(
                        "Office Name must be unique! This name is already used."))

    # ================================ Built-in Methods ================================

    def name_get(self):
        """
        Override name_get to show code and name.
        """
        result = []
        for office in self:
            if office.code:
                name = f"[{office.code}] {office.name}"
            else:
                name = office.name
            result.append((office.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Enhanced name search to find offices by name or code.
        """
        if name == '':
            return super().name_search(name, args, operator, limit)

        if args is None:
            args = []

        # Search by code first
        domain = [('code', operator, name)]
        offices = self.search(domain + args, limit=limit)
        if offices:
            return offices.name_get()

        # Then search by name
        domain = [('name', operator, name)]
        offices = self.search(domain + args, limit=limit)
        if offices:
            return offices.name_get()

        return super().name_search(name, args, operator, limit)

    # ================================ COMPUTE METHODS ================================

    @api.depends('student_ids')
    def _compute_student_count(self):
        """
        Compute the number of students in this office.
        """
        for office in self:
            office.student_count = len(office.student_ids)

    @api.depends('class_ids')
    def _compute_class_count(self):
        """
        Compute the number of classes in this office.
        """
        for office in self:
            office.class_count = len(office.class_ids)



    # ================================ ACTIONS ================================

    def action_view_students(self):
        """
        Action to view students in this office.
        """
        self.ensure_one()
        action = self.env.ref('management_quran_office_core.action_students_view_id').read()[0]
        action['domain'] = [('quran_office_id', '=', self.id)]
        action['context'] = {'default_quran_office_id': self.id}
        return action

    def action_view_classes(self):
        """
        Action to view classes in this office.
        """
        self.ensure_one()
        action = self.env.ref('management_quran_office_core.action_classes_view_id').read()[0]
        action['domain'] = [('office_id', '=', self.id)]
        action['context'] = {'default_office_id': self.id}
        return action
