# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class BatchSubscriptionWizard(models.TransientModel):
    _name = 'batch.subscription.wizard'
    _description = 'Batch Student Subscription Registration Wizard'

    subscription_month = fields.Date(
        string='Subscription Month',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
        help="Month and year for this subscription batch"
    )
    
    month_name = fields.Char(
        string='Month Name',
        compute='_compute_month_name',
        readonly=True
    )


    @api.depends('subscription_month')
    def _compute_month_name(self):
        """Compute month name for display"""
        for record in self:
            if record.subscription_month:
                record.month_name = record.subscription_month.strftime('%B %Y')
            else:
                record.month_name = ''

    def action_register_subscriptions(self):
        """Register subscriptions for all eligible students"""
        self.ensure_one()
        
        # Get all active students (including those without subscription fees for validation)
        active_ids= self._context.get('active_ids')
        all_active_students = self.env['res.partner'].browse(active_ids)

        # Check if any student has empty subscription fee
        students_without_fees = all_active_students.filtered(lambda s: s.subscription_fee <= 0)
        if students_without_fees:
            raise ValidationError(_("Cannot proceed with batch subscription registration. The following students do not have subscription fees set:\n\n") + '\n'.join(f"- {name}" for name in students_without_fees[:20]) + "\n\nPlease set subscription fees for all students before proceeding.")
        
        # Get all eligible students (now we know all have subscription fees)
        students = all_active_students.filtered(lambda s: s.subscription_fee > 0)

        subscription_vals_list = []
        # try:
        for student in students:
            discount_amount = student.subscription_fee * student.discount_percentage_fee
            expected_amount = student.subscription_fee - discount_amount
            subscription_vals = {
                'student_id': student.id,
                'subscription_month': self.subscription_month,
                'subscription_fee': student.subscription_fee,
                'discount_percentage_fee': student.discount_percentage_fee,
                'paid_amount': expected_amount,
            }

            subscription_vals_list.append(subscription_vals)
        self.env['monthly.subscription'].create(subscription_vals_list)

