# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class QuranClass(models.Model):
    _name = 'quran.office.class'
    _description = 'Quran Class'
    _order = 'name asc'

    name = fields.Char(
        'Class Name',
        required=True,
        help="Name of the class"
    )
    code = fields.Char('Code', readonly=True, default=lambda self: _('New'))
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
        'res.persons',
        'class_id',
        'Students',
        domain="[('is_student', '=', True)]",
        help="Students in this class"
    )

    teacher_id = fields.Many2one(
        'res.persons',
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

    _sql_constraints = [('office_name_uniq', "unique(name,office_id)", "Name must be unique per class per office."),]
    _rec_names_search = ['code', 'name']
    
# ================================ Built-in Methods ================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to generate registration number automatically."""
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('quran.office.class')
        return super().create(vals_list)

    @api.depends('name', 'code')
    def _compute_display_name(self):
        """Compute display name for class."""
        for cls in self:
            if cls.code:
                cls.display_name = f"[{cls.code}] {cls.name}"
            else:
                cls.display_name = cls.name

# ================================ CONSTRAINTS ================================
# ================================ COMPUTE METHODS ================================
    @api.depends('student_ids.is_student')
    def _compute_student_count(self):
        """Compute number of students in this class."""
        for cls in self:
            cls.student_count = len(cls.student_ids)

    # ================================ Actions ================================

    def action_view_students(self):
        """Action to view students in this class."""
        self.ensure_one()
        action = self.env.ref('management_quran_office_core.action_students_view_id').read()[0]
        action['domain'] = [('class_id', '=', self.id)]
        action['context'] = {'default_class_id': self.id}
        return action
