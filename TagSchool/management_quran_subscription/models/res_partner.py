# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class ResPartnerExtension(models.Model):
    _inherit = 'res.partner'

    # Subscription count for students
    subscription_count = fields.Integer(
        'Subscription Count',
        compute='_compute_subscription_count',
        help="Number of subscriptions for this student (only shown for students)"
    )



    def _compute_subscription_count(self):
        """
        Compute the number of subscriptions for this student (only for students)
        """
        for record in self:
            if record.is_student:
                # Count subscriptions where this partner is the student
                subscriptions = self.env['monthly.subscription'].search([('student_id', '=', record.id)])
                record.subscription_count = len(subscriptions)
            else:
                record.subscription_count = 0

    def action_view_subscriptions(self):
        """View subscriptions of this student"""
        self.ensure_one()
        name = _('Subscriptions of %s') % self.name
        domain = [('student_id', '=', self.id)]
        
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'monthly.subscription',
            'view_mode': 'list,form',
            'domain': domain,
            'context': { 'default_student_id': self.id, }
        }

    def action_create_subscription(self):
        """
        Open subscription registration form for the current student
        """
        self.ensure_one()
        
        # Check if the partner is a student
        if not self.is_student:
            raise ValidationError(_('This partner is not a student. Only students can have subscription records.'))
        
        # Check if student already has subscription for current month
        current_month = fields.Date.today().replace(day=1)
        existing_subscription = self.env['monthly.subscription'].search([
            ('student_id', '=', self.id),
            ('subscription_month', '>=', current_month)
        ], limit=1)
        
        if not existing_subscription:
            # Open new record
            return {
                'type': 'ir.actions.act_window',
                'name': _('Register Subscription'),
                'res_model': 'monthly.subscription',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_student_id': self.id,
                    'default_subscription_month': fields.Date.today(),
                }
            }
        else:
            raise ValidationError(_('This student already has subscription for current month.'))
