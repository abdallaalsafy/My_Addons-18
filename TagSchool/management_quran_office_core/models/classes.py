# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class QuranClass(models.Model):
    _name = 'quran_office.class'
    _description = 'Quran Class'
    _order = 'name asc'

    name = fields.Char(
        'Class Name',
        required=True,
        help="Name of the class"
    )
    
    code = fields.Char(
        'Class Code',
        help="Unique code for the class"
    )
    
    description = fields.Text(
        'Description',
        help="Additional information about the class"
    )
    
    active = fields.Boolean(
        'Active',
        default=True,
        help="If unchecked, this class will not be available"
    )
    
    # Relationships
    office_id = fields.Many2one(
        'quran.office.office',
        'Office',
        required=True,
        ondelete='cascade',
        help="Office this class belongs to"
    )
    
    student_ids = fields.One2many(
        'res.partner',
        'class_id',
        'Students',
        domain="[('is_student', '=', True)]",
        help="Students in this class"
    )

    teacher_id = fields.Many2one(
        'res.partner',
        'Teacher',
        domain="[('is_teacher', '=', True)]",
        help="Teacher or memorizer for this class"
    )
    
    student_count = fields.Integer(
        'Number of Students',
        compute='_compute_student_count',
        store=True,
        help="Total number of students in this class"
    )

    # ================================ Built-in Methods ================================

    def name_get(self):
        """
        Override name_get to show code and name.
        """
        result = []
        for cls in self:
            if cls.code:
                name = f"[{cls.code}] {cls.name}"
            else:
                name = cls.name
            result.append((cls.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Enhanced name search to find classes by name or code.
        """
        if name == '':
            return super().name_search(name, args, operator, limit)

        if args is None:
            args = []

        # Search by code first
        domain = [('code', operator, name)]
        classes = self.search(domain + args, limit=limit)
        if classes:
            return classes.name_get()

        # Then search by name
        domain = [('name', operator, name)]
        classes = self.search(domain + args, limit=limit)
        if classes:
            return classes.name_get()

        return super().name_search(name, args, operator, limit)

    # ================================ CONSTRAINTS ================================

    @api.constrains('code', 'office_id')
    def _check_unique_code(self):
        """
        Ensure class code is unique within the same office.
        """
        for cls in self:
            if cls.code:
                duplicates = self.search([
                    ('code', '=', cls.code),
                    ('office_id', '=', cls.office_id.id),
                    ('id', '!=', cls.id)
                ])
                if duplicates:
                    raise ValidationError(_(
                        "Class Code must be unique within the same office! This code is already used."))

    @api.constrains('name', 'office_id')
    def _check_unique_name(self):
        """
        Ensure class name is unique within the same office.
        """
        for cls in self:
            if cls.name:
                duplicates = self.search([
                    ('name', '=', cls.name),
                    ('office_id', '=', cls.office_id.id),
                    ('id', '!=', cls.id)
                ])
                if duplicates:
                    raise ValidationError(_(
                        "Class Name must be unique within the same office! This name is already used."))

    # ================================ COMPUTE METHODS ================================

    @api.depends('student_ids')
    def _compute_student_count(self):
        """
        Compute number of students in this class.
        """
        for cls in self:
            cls.student_count = len(cls.student_ids)

    # ================================ Actions ================================

    def action_view_students(self):
        """
        Action to view students in this class.
        """
        self.ensure_one()
        action = self.env.ref('management_quran_office_core.action_students_view_id').read()[0]
        action['domain'] = [('class_id', '=', self.id)]
        action['context'] = {'default_class_id': self.id}
        return action
