# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class QuranOffice(models.Model):
    _name = 'quran.office.office'
    _description = 'Quran Memorization Office'
    _order = 'name asc'

    name = fields.Char(
        'Name',
        required=True,
        help="Name of the Quran memorization office"
    )
    code = fields.Char('Code', readonly=True, default=lambda self: _('New'))
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
        'res.persons',
        'office_id',
        'Students',
        domain="[('is_student', '=', True)]",
        help="Students in this office"
    )
    
    class_ids = fields.One2many(
        'quran.office.class',
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

    _sql_constraints = [('name_uniq', "unique(name)", "Name must be unique per office."),]
    # Many2one autocomplete / search by code or name (replaces the old name_search override)
    _rec_names_search = ['code', 'name']
    

# ================================ Built-in Methods ================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to generate registration number automatically."""
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('quran.office.office')

        return super(QuranOffice, self).create(vals_list)

    @api.depends('name', 'code')
    def _compute_display_name(self):
        """Override _compute_display_name to show code and name."""
        for office in self:
            office.display_name = f"[{office.code}] {office.name}"

    # ================================ COMPUTE METHODS ================================

    @api.depends('student_ids.is_student')
    def _compute_student_count(self):
        """Compute the number of students in this office."""
        for office in self:
            office.student_count = len(office.student_ids)

    @api.depends('class_ids')
    def _compute_class_count(self):
        """Compute the number of classes in this office."""
        for office in self:
            office.class_count = len(office.class_ids)

    # ================================ ACTIONS ================================

    def action_view_students(self):
        """Action to view students in this office."""
        self.ensure_one()
        action = self.env.ref('management_quran_office_core.action_students_view_id').read()[0]
        action['domain'] = [('office_id', '=', self.id)]
        action['context'] = {'default_office_id': self.id}
        return action

    def action_view_classes(self):
        """Action to view classes in this office."""
        self.ensure_one()
        action = self.env.ref('management_quran_office_core.action_classes_view_id').read()[0]
        action['domain'] = [('office_id', '=', self.id)]
        action['context'] = {'default_office_id': self.id}
        return action
