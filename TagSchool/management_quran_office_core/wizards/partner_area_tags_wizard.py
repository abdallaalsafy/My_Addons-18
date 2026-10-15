# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PartnerAreaTagsWizard(models.TransientModel):
    _name = 'partner.area.tags.wizard'
    _description = 'Partner Area Tags Wizard'
    
    # Boolean fields to control which fields to update
    update_area = fields.Boolean(
        'Update Area',
        help="Check to update area information"
    )
    
    update_tags = fields.Boolean(
        'Update Tags', 
        help="Check to update tags information"
    )
    
    # Data fields
    area_id = fields.Many2one(
        'quran_office.area',
        'Area',
        help="Select area for partners"
    )
    
    tag_ids = fields.Many2many(
        'res.partner.category',
        'partner_area_tags_wizard_category_rel',
        'wizard_id',
        'category_id',
        string='Tags',
        help="Tags to add to partners"
    )
    
    tags_mode = fields.Selection([
        ('add', 'Add Tags'),
        ('replace', 'Replace Tags'),
    ], string='Tags Mode', default='add', required=True,
       help="Add tags to existing ones or replace all tags")
    
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
            self.update_area = False
            self.update_tags = False

    def action_apply_area_tags(self):
        """
        Apply area and tags changes to selected partners based on mode and selected fields
        """
        # Get partners from active_ids
        active_ids = self._context.get('active_ids')
        if not active_ids or self._context.get('active_model') != 'res.partner':
            raise ValidationError(_('This wizard must be called from partner list view'))
        
        partners = self.env['res.partner'].browse(active_ids)
        
        # Check if at least one field is selected for update
        if self.mode == 'update' and not any([self.update_area, self.update_tags]):
            raise ValidationError(_('Please select at least one field to update'))
        
        for partner in partners:
            update_values = {}
            
            if self.mode == 'update':
                # Update only selected fields
                if self.update_area:
                    update_values['area_id'] = self.area_id.id if self.area_id else False
                
                if self.update_tags:
                    if self.tags_mode == 'add':
                        # Add tags to existing ones
                        current_tag_ids = partner.category_id.ids
                        new_tag_ids = list(set(current_tag_ids + self.tag_ids.ids))
                        update_values['category_id'] = [(6, 0, new_tag_ids)]
                    elif self.tags_mode == 'replace':
                        # Replace all tags
                        update_values['category_id'] = [(6, 0, self.tag_ids.ids)]

            elif self.mode == 'clear':
                # Clear all selected fields
                if self.update_area:
                    update_values['area_id'] = False
                if self.update_tags:
                    update_values['category_id'] = [(6, 0, [])]

            if update_values:
                partner.write(update_values)
