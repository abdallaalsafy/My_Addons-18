# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PartnerQualificationWizard(models.TransientModel):
    _name = 'partner.qualification.wizard'
    _description = 'Partner Qualification Wizard'
    
    qualification = fields.Char(
        string='Qualification',
        help="Enter the academic qualification for partners"
    )
    
    mode = fields.Selection([
        ('update', 'Update Qualification'),
        ('clear', 'Clear Qualification'),
    ], string='Mode', default='update', required=True,
       help="Update qualification or clear existing qualification")

    def action_apply_qualification(self):
        """
        Apply academic qualification change to selected partners based on mode
        """
        # Get partners from active_ids
        active_ids = self._context.get('active_ids')
        if not active_ids or self._context.get('active_model') != 'res.partner':
            raise ValidationError(_('This wizard must be called from partner list view'))
        
        partners = self.env['res.partner'].browse(active_ids)
        
        for partner in partners:
            if self.mode == 'update':
                # Update academic qualification
                partner.write({'qualification': self.qualification})
            elif self.mode == 'clear':
                # Clear existing academic qualification
                partner.write({'qualification': False})
