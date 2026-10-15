# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StudentSubscriptionWizard(models.TransientModel):
    _name = 'student.subscription.wizard'
    _description = 'Student Subscription Wizard'
    
    # Boolean fields to control which fields to update
    update_subscription_fee = fields.Boolean(
        'Update Subscription Fee',
        help="Check to update subscription fee"
    )
    
    update_discount = fields.Boolean(
        'Update Discount', 
        help="Check to update discount information"
    )
    
    # Data fields
    subscription_fee = fields.Float(
        'Subscription Fee',
        digits=(10, 2),
        help="Student subscription fee"
    )
    
    discount_percentage_fee = fields.Float(
        'Discount Percentage',
        digits=(5, 2),
        help="Discount percentage for student subscription fee"
    )
    
    reason_discount_fee = fields.Char(
        'Reason for Discount',
        help="Reason for discount on student subscription fee"
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
            self.update_subscription_fee = False
            self.update_discount = False

    @api.onchange('discount_percentage_fee')
    def _onchange_discount_percentage_fee(self):
        """
        Clear reason when discount is zero
        """
        if self.discount_percentage_fee == 0:
            self.reason_discount_fee = False

    def action_apply_subscription(self):
        """
        Apply subscription changes to selected students based on mode and selected fields
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
        if self.mode == 'update' and not any([self.update_subscription_fee, self.update_discount]):
            raise ValidationError(_('Please select at least one field to update'))
        
        for partner in partners:
            update_values = {}
            
            if self.mode == 'update':
                # Update only selected fields
                if self.update_subscription_fee:
                    update_values['subscription_fee'] = self.subscription_fee
                
                if self.update_discount:
                    update_values['discount_percentage_fee'] = self.discount_percentage_fee
                    update_values['reason_discount_fee'] = self.reason_discount_fee

            elif self.mode == 'clear':
                # Clear all selected fields
                if self.update_subscription_fee:
                    update_values['subscription_fee'] = 0.0
                if self.update_discount:
                    update_values['discount_percentage_fee'] = 0.0
                    update_values['reason_discount_fee'] = False

            if update_values:
                partner.write(update_values)
