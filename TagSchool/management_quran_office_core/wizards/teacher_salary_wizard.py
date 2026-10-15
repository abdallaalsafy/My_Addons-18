# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TeacherSalaryWizard(models.TransientModel):
    _name = 'teacher.salary.wizard'
    _description = 'Teacher Salary Wizard'
    
    # Boolean field to control which fields to update
    update_teacher_salary = fields.Boolean(
        'Update Teacher Salary',
        help="Check to update teacher salary"
    )
    
    # Data field
    teacher_salary = fields.Float(
        'Teacher Salary',
        digits=(10, 2),
        help="Teacher monthly salary"
    )
    
    mode = fields.Selection([
        ('update', 'Update Fields'),
        ('clear', 'Clear Fields'),
    ], string='Mode', default='update', required=True,
       help="Update selected fields or clear existing data")

    @api.onchange('mode')
    def _onchange_mode(self):
        """
        Clear checkboxes when switching to clear mode
        """
        if self.mode == 'clear':
            self.update_teacher_salary = False

    def action_apply_salary(self):
        """
        Apply salary changes to selected teachers based on mode and selected fields
        """
        # Get partners from active_ids
        active_ids = self._context.get('active_ids')
        if not active_ids or self._context.get('active_model') != 'res.partner':
            raise ValidationError(_('This wizard must be called from partner list view'))
        
        partners = self.env['res.partner'].browse(active_ids)
        
        # Check if all selected partners are teachers
        for partner in partners:
            if not partner.is_teacher:
                raise ValidationError(_('This wizard can only be used for teachers. Partner %s is not a teacher.') % partner.name)
        
        # Check if at least one field is selected for update
        if self.mode == 'update' and not self.update_teacher_salary:
            raise ValidationError(_('Please select at least one field to update'))
        
        for partner in partners:
            update_values = {}
            
            if self.mode == 'update':
                # Update only selected fields
                if self.update_teacher_salary:
                    update_values['teacher_salary'] = self.teacher_salary
                    
            elif self.mode == 'clear':
                # Clear all selected fields
                if self.update_teacher_salary:
                    update_values['teacher_salary'] = 0.0
            
            if update_values:
                partner.write(update_values)
