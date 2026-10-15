# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StudentAcademicWizard(models.TransientModel):
    _name = 'student.academic.wizard'
    _description = 'Student Academic Wizard'
    
    # Boolean fields to control which fields to update
    update_office_class = fields.Boolean(
        'Update Office & Class',
        help="Check to update office information"
    )
    
    update_teacher = fields.Boolean(
        'Update Teacher',
        help="Check to update teacher information"
    )
    
    # Data fields
    office_id = fields.Many2one(
        'quran_office.office',
        'Office',
        help="Select office for student"
    )
    
    class_id = fields.Many2one(
        'quran_office.class',
        'Class',
        domain="[('office_id', '=?', office_id)]",
        help="Select class for student"
    )
    
    teacher_id = fields.Many2one(
        'res.partner',
        'Teacher',
        domain="[('is_teacher', '=', True)]",
        help="Select teacher for student"
    )
    
    mode = fields.Selection([
        ('update', 'Update Fields'),
        ('clear', 'Clear Fields'),
    ], string='Mode', default='update', required=True,
       help="Update selected fields or clear existing data")

    @api.onchange('office_id')
    def _onchange_office_id(self):
        """
        Clear class_id and teacher_id when office changes to ensure proper filtering.
        """
        if (self.office_id and self.office_id != self.class_id.office_id) or not self.office_id:
            self.class_id = False

    @api.onchange('class_id')
    def _onchange_class_id(self):
        """
        Auto-fill teacher_id when class is selected.
        """
        if self.class_id:
            self.office_id = self.class_id.office_id
        if self.class_id and self.class_id.teacher_id:
            self.teacher_id = self.class_id.teacher_id

    @api.onchange('teacher_id')
    def _onchange_teacher_id(self):
        if self.teacher_id and not self.class_id:
            self.class_id = self.teacher_id.class_ids[0]

    @api.onchange('mode')
    def _onchange_mode(self):
        """
        Clear checkboxes when switching to clear mode
        """
        if self.mode == 'clear':
            self.update_office_class = False
            self.update_teacher = False

    def action_apply_academic_info(self):
        """
        Apply academic information changes to selected students based on mode and selected fields
        """
        # Get partners from active_ids
        active_ids = self._context.get('active_ids')
        if not active_ids or self._context.get('active_model') != 'res.partner':
            raise ValidationError(_('This wizard must be called from partner list view'))
        
        partners = self.env['res.partner'].browse(active_ids)
        
        # Check if all selected partners are students
        for partner in partners:
            if not partner.is_student:
                raise ValidationError(_('This wizard can only be used for students. Partner %s is not a student.') % partner.name)
        
        # Check if at least one field is selected for update
        if self.mode == 'update' and not any([self.update_office_class, self.update_teacher]):
            raise ValidationError(_('Please select at least one field to update'))
        
        for partner in partners:
            update_values = {}
            
            if self.mode == 'update':
                # Update only selected fields
                if self.update_office_class:
                    update_values['office_id'] = self.office_id.id if self.office_id else False
                    update_values['class_id'] = self.class_id.id if self.class_id else False
                
                if self.update_teacher:
                    update_values['teacher_id'] = self.teacher_id.id if self.teacher_id else False
                    
            elif self.mode == 'clear':
                # Clear all academic fields
                update_values = {
                    'office_id': False,
                    'class_id': False,
                    'teacher_id': False,
                }
            
            if update_values:
                partner.write(update_values)
