# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class BatchSubscriptionWizard(models.TransientModel):
    _name = 'batch.subscription.wizard'
    _inherit = ['school.organization.mixin']
    _description = 'Batch Student Subscription Registration Wizard'


    def _get_defaults_values(self):
        """Get default values for the wizard fields based on the context."""
        defaults = {}
        active_ids = self._context.get('active_ids', [])
        if len(active_ids) == 1:
            students = self.env['res.partner'].browse(active_ids)
            if len(students) == 1:
                student = students[0]
                defaults['office_id'] = student.office_id
                defaults['class_id'] = student.class_id
                defaults['teacher_id'] = student.teacher_id
                defaults['subscription_fee'] = student.get_subscription_expected_amount()
        return defaults

    subscription_month = fields.Date(
        string='Subscription Month',
        required=True,
        default=lambda self: fields.Date.today(),
        help="Month and year for this subscription batch"
    )
    month_name = fields.Char(
        string='Month Name',
        compute='_compute_month_name',
        readonly=True
    )
    office_id = fields.Many2one(default=lambda self: self._get_defaults_values().get('office_id'),)
    class_id = fields.Many2one(default=lambda self: self._get_defaults_values().get('class_id'),)
    teacher_id = fields.Many2one(default=lambda self: self._get_defaults_values().get('teacher_id'),
                                 )
    subscription_fee = fields.Monetary(
        string='Subscription Fee',
        currency_field='currency_id',
        default=lambda self: self._get_defaults_values().get('subscription_fee'),
        help="Student subscription fee"
    )
    currency_id = fields.Many2one(
        'res.currency',
        'Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Currency for subscription fee"
    )


# ========================= Computed Functions =========================
    @api.depends('subscription_month')
    def _compute_month_name(self):
        """Compute month name for display"""
        for record in self:
            if record.subscription_month:
                record.month_name = record.subscription_month.strftime('%B %Y')
            else:
                record.month_name = ''

# ========================= Action Functions =========================
    def action_register_subscriptions(self):
        """Register subscriptions for all eligible students"""
        active_ids= self._context.get('active_ids')
        students = self.env['res.partner'].browse(active_ids)

        subscription_vals_list = []
        for student in students:
            subscription_month = self.subscription_month
            subscription_fee = self.subscription_fee or student.get_subscription_expected_amount()
            office_id = self.office_id or student.office_id
            class_id = self.class_id or student.class_id
            teacher = self.teacher_id or student.teacher_id
            student.validate_student_for_subscription(office=office_id, subscription_fee=subscription_fee)

            subscription_vals_list.append({
                'student_id': student.id,
                'subscription_month': subscription_month,
                'office_id': office_id.id,
                'class_id': class_id.id,
                'teacher_id': teacher.id,
                'paid_amount': subscription_fee,
            })

        self.env['monthly.subscription'].create(subscription_vals_list)

