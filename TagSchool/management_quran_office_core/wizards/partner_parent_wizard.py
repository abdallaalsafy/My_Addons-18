# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PartnerParentWizard(models.TransientModel):
    _name = 'partner.parent.wizard'
    _description = 'Partner Parent Wizard'
    
    # Boolean fields to control which fields to update
    update_father = fields.Boolean(
        'Update Father',
        help="Check to update father information"
    )
    
    update_mother = fields.Boolean(
        'Update Mother', 
        help="Check to update mother information"
    )
    
    update_orphan_status = fields.Boolean(
        'Update Orphan Status',
        help="Check to update orphan status"
    )
    
    # Data fields
    father_name = fields.Many2one(
        'res.partner',
        'Father Name',
        domain="[('parent_role', '=', 'father')]",
        help="Select the father from existing partners"
    )
    
    mother_name = fields.Many2one(
        'res.partner',
        'Mother Name',
        domain="[('parent_role', '=', 'mother')]",
        help="Select the mother from existing partners"
    )
    
    is_fatherless = fields.Boolean(
        'Fatherless',
        help="Is the student fatherless"
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
            self.update_father = False
            self.update_mother = False
            self.update_orphan_status = False

    def action_apply_parent_info(self):
        """
        Apply parent information changes to selected partners based on mode and selected fields
        """
        # Get partners from active_ids
        active_ids = self._context.get('active_ids')
        if not active_ids or self._context.get('active_model') != 'res.partner':
            raise ValidationError(_('This wizard must be called from partner list view'))
        
        partners = self.env['res.partner'].browse(active_ids)
        
        # Check if at least one field is selected for update
        if self.mode == 'update' and not any([self.update_father, self.update_mother, self.update_orphan_status]):
            raise ValidationError(_('Please select at least one field to update'))
        
        for partner in partners:
            update_values = {}
            
            if self.mode == 'update':
                # Update only selected fields
                if self.update_father:
                    update_values['father_name'] = self.father_name.id if self.father_name else False
                
                if self.update_mother:
                    update_values['mother_name'] = self.mother_name.id if self.mother_name else False
                
                if self.update_orphan_status:
                    update_values['is_fatherless'] = self.is_fatherless
                    
            elif self.mode == 'clear':
                # Clear all parent fields
                update_values = {
                    'father_name': False,
                    'mother_name': False,
                    'is_fatherless': False,
                }
            
            if update_values:
                partner.write(update_values)
